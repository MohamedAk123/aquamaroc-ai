FROM python:3.12.12-slim@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.lock
COPY services ./services
COPY pipelines ./pipelines
COPY config ./config
COPY alembic.ini ./
COPY data/demo ./data/demo
RUN useradd --create-home --uid 10001 aquamaroc && mkdir -p /app/data/archive \
    && chown -R aquamaroc:aquamaroc /app
USER aquamaroc
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
