"""
Métricas en memoria. Para producción a escala, reemplazar con Prometheus.
"""
import time
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self.total_requests: int = 0
        self.total_errors: int = 0
        self.requests_by_model: dict[str, int] = defaultdict(int)
        self.latency_sum: float = 0.0
        self.latency_count: int = 0
        self._start_time: float = time.time()

    def record_request(self, model: str, latency_seconds: float, error: bool = False) -> None:
        with self._lock:
            self.total_requests += 1
            self.requests_by_model[model] += 1
            self.latency_sum += latency_seconds
            self.latency_count += 1
            if error:
                self.total_errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency = (
                round(self.latency_sum / self.latency_count, 3)
                if self.latency_count > 0 else 0.0
            )
            return {
                "uptime_seconds": round(time.time() - self._start_time, 1),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "success_rate": (
                    round((self.total_requests - self.total_errors) / self.total_requests, 4)
                    if self.total_requests > 0 else 1.0
                ),
                "avg_latency_seconds": avg_latency,
                "requests_by_model": dict(self.requests_by_model),
            }


# Singleton global
metrics = MetricsCollector()
