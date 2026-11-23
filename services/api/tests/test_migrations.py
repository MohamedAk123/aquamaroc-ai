from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text


def test_initial_migration_upgrade_and_downgrade(engine):
    tables = set(inspect(engine).get_table_names())
    assert tables == {
        "alembic_version",
        "basins",
        "reservoirs",
        "data_sources",
        "ingestion_runs",
        "reservoir_measurements",
        "quality_issues",
    }
    assert len(inspect(engine).get_check_constraints("reservoir_measurements")) >= 4
    with engine.connect() as db:
        assert (
            db.scalar(text("SELECT version_num FROM alembic_version")) == "0002_capacity_provenance"
        )
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    command.upgrade(config, "head")
