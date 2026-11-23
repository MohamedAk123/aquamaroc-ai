.PHONY: install test lint up migrate demo
install:
	python -m pip install -r requirements-dev.lock
	python -m pip install --no-deps -e .
test:
	python -m pytest -q
lint:
	python -m ruff check .
	python -m ruff format --check .
up:
	docker compose up --build -d
migrate:
	python -m alembic upgrade head
demo:
	python -m pipelines.ingestion.demo
	python -m pipelines.ingestion.import_xlsx --file data/demo/reservoirs_demo.xlsx --source-id 00000000-0000-0000-0000-000000000001
