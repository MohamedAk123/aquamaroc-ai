"""Sauvegarde PostgreSQL et archives XLSX, avec répétition de restauration isolée."""

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

STATS_SQL = """
SELECT json_build_object(
  'official', count(*) FILTER (WHERE data_kind = 'OFFICIAL'),
  'demo', count(*) FILTER (WHERE data_kind = 'DEMO'),
  'unverified', count(*) FILTER (WHERE data_kind = 'UNVERIFIED'),
  'first_date', min(observation_date) FILTER (WHERE data_kind = 'OFFICIAL'),
  'last_date', max(observation_date) FILTER (WHERE data_kind = 'OFFICIAL'),
  'measurement_fingerprint', md5(coalesce(string_agg(
    json_build_array(id, reservoir_id, observation_date, storage_mm3, filling_rate_pct,
      data_kind, source_id, ingestion_run_id, published_at, ingested_at, quality_status)::text,
    chr(10) ORDER BY id), ''))
) FROM reservoir_measurements
"""
FILES = ("database.dump", "archives.tar.gz")


def run(command: list[str], **kwargs):
    return subprocess.run(command, check=True, **kwargs)


def file_hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def psql(compose: list[str], user: str, db: str, sql: str) -> str:
    return run(
        [
            *compose,
            "exec",
            "-T",
            "db",
            "psql",
            "-XAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            user,
            "-d",
            db,
            "-c",
            sql,
        ],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def archive_digests(compose: list[str], user: str, db: str) -> set[str]:
    return set(psql(compose, user, db, "SELECT DISTINCT sha256 FROM ingestion_runs").splitlines())


def verify_archives(path: Path, expected: set[str]) -> None:
    found = set()
    with tarfile.open(path, "r:gz") as archive:
        for member in archive:
            name = member.name.removeprefix("./")
            if member.isdir() and name in {"", "."}:
                continue
            if not member.isfile() or not re.fullmatch(r"[a-f0-9]{64}\.xlsx", name):
                raise ValueError(f"Entrée inattendue dans l’archive : {member.name}")
            expected_hash = name.removesuffix(".xlsx")
            content = archive.extractfile(member)
            if content is None:
                raise ValueError(f"Archive illisible : {name}")
            with content:
                actual_hash = hashlib.file_digest(content, "sha256").hexdigest()
            if expected_hash != actual_hash or actual_hash in found:
                raise ValueError(f"Archive XLSX modifiée ou en double : {name}")
            found.add(actual_hash)
    if not expected <= found:
        raise ValueError(f"{len(expected - found)} archive(s) originale(s) manquante(s)")


def backup(compose: list[str], user: str, db: str, directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    before = json.loads(psql(compose, user, db, STATS_SQL))
    digests = archive_digests(compose, user, db)
    with (directory / FILES[0]).open("xb") as out:
        run(
            [
                *compose,
                "exec",
                "-T",
                "db",
                "pg_dump",
                "-U",
                user,
                "--format=custom",
                "--no-owner",
                "--no-acl",
                "-d",
                db,
            ],
            stdout=out,
        )
    with (directory / FILES[1]).open("xb") as out:
        run(
            [
                *compose,
                "exec",
                "-T",
                "api",
                "tar",
                "-czf",
                "-",
                "-C",
                "/app/data/archive",
                ".",
            ],
            stdout=out,
        )
    if json.loads(psql(compose, user, db, STATS_SQL)) != before:
        raise ValueError(
            "Relevés modifiés pendant la sauvegarde. Suspendre les imports et réessayer."
        )
    if archive_digests(compose, user, db) != digests:
        raise ValueError("Journal modifié pendant la sauvegarde. Suspendre les imports.")
    verify_archives(directory / FILES[1], digests)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "files": {name: file_hash(directory / name) for name in FILES},
        "measurements": before,
        "source_archives": sorted(digests),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_backup(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for name in FILES:
        if file_hash(directory / name) != manifest["files"][name]:
            raise ValueError(f"Empreinte de sauvegarde incorrecte : {name}")
    verify_archives(directory / FILES[1], set(manifest["source_archives"]))
    return manifest


def restore_database(compose: list[str], user: str, db: str, directory: Path, manifest: dict):
    with (directory / FILES[0]).open("rb") as stream:
        run(
            [
                *compose,
                "exec",
                "-T",
                "db",
                "pg_restore",
                "-U",
                user,
                "--exit-on-error",
                "--single-transaction",
                "--no-owner",
                "--no-acl",
                "-d",
                db,
            ],
            stdin=stream,
        )
    actual = json.loads(psql(compose, user, db, STATS_SQL))
    if actual != manifest["measurements"]:
        raise ValueError("Les relevés restaurés diffèrent de la sauvegarde")
    if archive_digests(compose, user, db) != set(manifest["source_archives"]):
        raise ValueError("Provenance restaurée incohérente")
    return {"status": "restored_and_verified", **actual}


def rehearse(compose: list[str], user: str, directory: Path) -> dict:
    manifest = verify_backup(directory)
    isolated = f"aquamaroc_restore_{uuid4().hex}"
    command = [*compose, "exec", "-T", "db"]
    run([*command, "createdb", "-U", user, isolated])
    try:
        return restore_database(compose, user, isolated, directory, manifest)
    finally:
        # Cette commande ne cible que la base temporaire créée dans cette fonction.
        run([*command, "dropdb", "-U", user, isolated])


def recover(compose: list[str], user: str, db: str, directory: Path) -> dict:
    """Reconstruit une installation dans une nouvelle base et un volume d’archives vide."""
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", db):
        raise ValueError("Nom de nouvelle base invalide")
    manifest = verify_backup(directory)
    existing = psql(
        compose,
        user,
        "postgres",
        f"SELECT count(*) FROM pg_database WHERE datname='{db}'",
    )
    if existing != "0":
        raise ValueError("La restauration complète exige un nom de base encore inutilisé")
    api_run = [*compose, "run", "--rm", "--no-deps", "-T", "--entrypoint"]
    listing = run(
        [*api_run, "find", "api", "/app/data/archive", "-mindepth", "1", "-maxdepth", "1"],
        stdout=subprocess.PIPE,
    ).stdout
    if listing.strip():
        raise ValueError("La restauration complète exige un volume d’archives vide")
    run([*compose, "exec", "-T", "db", "createdb", "-U", user, "-T", "template0", db])
    result = restore_database(compose, user, db, directory, manifest)
    with (directory / FILES[1]).open("rb") as stream:
        run(
            [
                *api_run,
                "tar",
                "api",
                "--keep-old-files",
                "--no-same-owner",
                "-xzf",
                "-",
                "-C",
                "/app/data/archive",
            ],
            stdin=stream,
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("backup", "rehearse", "recover"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--docker-config")
    parser.add_argument("--compose-file", default="docker-compose.prod.yml")
    parser.add_argument("--env-file", default=".env.prod")
    parser.add_argument("--project", default="aquamaroc-prod")
    parser.add_argument("--user", default="aquamaroc")
    parser.add_argument("--database", default="aquamaroc")
    args = parser.parse_args()
    compose = ["docker"]
    if args.docker_config:
        compose.extend(["--config", args.docker_config])
    compose.extend(
        [
            "compose",
            "--project-name",
            args.project,
            "--file",
            args.compose_file,
            "--env-file",
            args.env_file,
        ]
    )
    if args.action == "rehearse":
        result = rehearse(compose, args.user, args.directory)
    else:
        action = backup if args.action == "backup" else recover
        result = action(compose, args.user, args.database, args.directory)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
