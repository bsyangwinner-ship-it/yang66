from collections import defaultdict
from collections.abc import Awaitable, Callable
from importlib import import_module
from threading import Lock
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request, Response

from app.core.config import settings

CallNext = Callable[[Request], Awaitable[Response]]


class HttpMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._request_total: defaultdict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_sum: defaultdict[tuple[str, str, int], float] = defaultdict(float)

    def record(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        key = (method.upper(), path, status_code)
        with self._lock:
            self._request_total[key] += 1
            self._duration_sum[key] += duration_seconds

    def render_prometheus(self) -> str:
        lines = [
            "# HELP nutrition_agent_app_info Application build and environment information.",
            "# TYPE nutrition_agent_app_info gauge",
            (
                'nutrition_agent_app_info{service="'
                f'{_escape_label(settings.app_name)}",version="{_escape_label(settings.app_version)}",'
                f'environment="{_escape_label(settings.environment)}"}} 1'
            ),
            "# HELP nutrition_agent_http_requests_total Total HTTP requests.",
            "# TYPE nutrition_agent_http_requests_total counter",
        ]
        with self._lock:
            request_items = list(self._request_total.items())
            duration_items = list(self._duration_sum.items())

        for (method, path, status_code), count in request_items:
            labels = _labels(method, path, status_code)
            lines.append(f"nutrition_agent_http_requests_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP nutrition_agent_http_request_duration_seconds_sum Total request duration.",
                "# TYPE nutrition_agent_http_request_duration_seconds_sum counter",
            ]
        )
        for (method, path, status_code), duration in duration_items:
            labels = _labels(method, path, status_code)
            lines.append(
                f"nutrition_agent_http_request_duration_seconds_sum{{{labels}}} {duration:.6f}"
            )

        lines.extend(
            [
                "# HELP nutrition_agent_http_request_duration_seconds_count "
                "Request duration sample count.",
                "# TYPE nutrition_agent_http_request_duration_seconds_count counter",
            ]
        )
        for (method, path, status_code), count in request_items:
            labels = _labels(method, path, status_code)
            lines.append(
                f"nutrition_agent_http_request_duration_seconds_count{{{labels}}} {count}"
            )

        return "\n".join(lines) + "\n"


http_metrics = HttpMetrics()


def _escape_label(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _labels(method: str, path: str, status_code: int) -> str:
    return (
        f'method="{_escape_label(method)}",'
        f'path="{_escape_label(path)}",'
        f'status="{status_code}"'
    )


async def metrics_middleware(request: Request, call_next: CallNext) -> Response:
    if not settings.prometheus_enabled or request.url.path == "/metrics":
        return await call_next(request)

    started = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        http_metrics.record(
            request.method,
            request.url.path,
            status_code,
            perf_counter() - started,
        )


def configure_optional_opentelemetry(app: FastAPI) -> None:
    if not settings.otel_enabled:
        return

    try:
        resources_module = import_module("opentelemetry.sdk.resources")
        sdk_trace_module = import_module("opentelemetry.sdk.trace")
        export_module = import_module("opentelemetry.sdk.trace.export")
        otlp_module = import_module("opentelemetry.exporter.otlp.proto.grpc.trace_exporter")
        trace_module = import_module("opentelemetry.trace")
        fastapi_module = import_module("opentelemetry.instrumentation.fastapi")
    except Exception:
        return

    resource_attr = "Resource"
    tracer_provider_attr = "TracerProvider"
    span_processor_attr = "BatchSpanProcessor"
    exporter_attr = "OTLPSpanExporter"
    set_provider_attr = "set_tracer_provider"
    instrumentor_attr = "FastAPIInstrumentor"

    resource_factory = getattr(resources_module, resource_attr)
    tracer_provider_factory = getattr(sdk_trace_module, tracer_provider_attr)
    span_processor_factory = getattr(export_module, span_processor_attr)
    exporter_factory = getattr(otlp_module, exporter_attr)
    set_tracer_provider = getattr(trace_module, set_provider_attr)
    instrumentor_factory: Any = getattr(fastapi_module, instrumentor_attr)

    resource = resource_factory.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": settings.environment,
        }
    )
    tracer_provider = tracer_provider_factory(resource=resource)
    tracer_provider.add_span_processor(
        span_processor_factory(
            exporter_factory(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        )
    )
    set_tracer_provider(tracer_provider)
    instrumentor_factory.instrument_app(app)
