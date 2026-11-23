"""Métriques techniques à cardinalité bornée, sans données d'utilisateur."""

from time import perf_counter

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Histogram,
    ProcessCollector,
    generate_latest,
)


def install_metrics(app: FastAPI) -> None:
    registry = CollectorRegistry()
    ProcessCollector(registry=registry)
    latency = Histogram(
        "aquamaroc_http_request_duration_seconds",
        "Durée des requêtes HTTP.",
        ("route", "status"),
        registry=registry,
    )

    @app.middleware("http")
    async def observe(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        start = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = getattr(request.scope.get("route"), "path", None) or "unmatched"
            latency.labels(route=route, status=str(status)).observe(perf_counter() - start)

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(registry), headers={"Content-Type": CONTENT_TYPE_LATEST})
