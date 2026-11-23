"""Connect to a temporary H2O server with native XGBoost support."""

import subprocess
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path
from platform import system
from shutil import which
from time import monotonic, sleep
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener
from uuid import uuid4

JAVA_IMAGE = (
    "eclipse-temurin@sha256:aa6381384f8db99762fa7d0d3c2b5de58874e5f12c96df4c13a1455376ae0ed1"
)


def docker_output(docker: str, *args: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            [docker, *args], check=True, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout).strip()
        raise RuntimeError(f"Docker {args[0]} a échoué. {detail}") from error
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(f"Délai dépassé pour Docker {args[0]}.") from error
    return result.stdout.strip()


def wait_for_server(url: str) -> None:
    opener = build_opener(ProxyHandler({}))
    deadline = monotonic() + 120
    while monotonic() < deadline:
        try:
            with opener.open(f"{url}/3/Cloud", timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, ConnectionError, TimeoutError):
            pass
        sleep(0.5)
    raise RuntimeError("H2O n’a pas démarré dans le délai prévu.")


@contextmanager
def docker_server(jar: Path) -> Iterator[str]:
    docker = which("docker")
    if docker is None:
        raise RuntimeError("H2O avec XGBoost sous Windows exige Docker en mode conteneurs Linux.")
    name = f"aquamaroc-h2o-{uuid4().hex}"
    started = False
    try:
        docker_output(
            docker,
            "run",
            "--detach",
            "--name",
            name,
            "--platform",
            "linux/amd64",
            "--publish",
            "127.0.0.1::54321",
            "--mount",
            f"type=bind,source={jar},target=/opt/h2o.jar,readonly",
            JAVA_IMAGE,
            "java",
            "-Xmx1g",
            "-jar",
            "/opt/h2o.jar",
            "-web_ip",
            "0.0.0.0",
            "-name",
            name,
            "-nthreads",
            "1",
            timeout=180,
        )
        started = True
        address = docker_output(docker, "port", name, "54321/tcp")
        host, _, port = address.rpartition(":")
        if host != "127.0.0.1" or not port.isdigit():
            raise RuntimeError("Docker n’a pas attribué de port local à H2O.")
        url = f"http://{address}"
        try:
            wait_for_server(url)
        except RuntimeError as error:
            logs = docker_output(docker, "logs", "--tail", "20", name)
            raise RuntimeError(f"{error}\n{logs}") from error
        yield url
    finally:
        try:
            docker_output(docker, "rm", "--force", name)
        except RuntimeError as error:
            if started:
                warnings.warn(str(error), RuntimeWarning, stacklevel=2)


@contextmanager
def h2o_connection() -> Iterator[str]:
    import h2o

    if system() == "Windows":
        jar = files("h2o").joinpath("backend", "bin", "h2o.jar")
        if not jar.is_file():
            raise RuntimeError("JAR H2O introuvable. Installer l’extra automl-h2o.")
        with as_file(jar) as jar_path, docker_server(jar_path) as url:
            with h2o.connect(url=url, verbose=False):
                yield "docker-linux-amd64"
    else:
        from h2o.backend import H2OLocalServer

        with H2OLocalServer.start(nthreads=1, bind_to_localhost=True, verbose=False) as server:
            with h2o.connect(server=server, verbose=False):
                yield "native"
