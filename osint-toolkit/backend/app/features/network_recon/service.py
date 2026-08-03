"""Provider-agnostic network reconnaissance orchestration and TTL caching."""

from collections.abc import Callable
import time
from typing import Any, Protocol

from app.core.logging import get_logger
from app.features.network_recon.client import ShodanClient
from app.features.network_recon.schemas import HostData, Location, SearchData, SearchHost, ServiceBanner


logger = get_logger(__name__)
HOST_CACHE_TTL_SECONDS = 300.0
_host_cache: dict[str, tuple[float, HostData]] = {}


class ShodanProvider(Protocol):
    """Provider contract used by the service and test doubles."""

    def host(self, ip: str) -> dict[str, Any]: ...

    def search(self, query: str, page: int) -> dict[str, Any]: ...


class NetworkReconService:
    """Coordinate Shodan queries and map provider data into stable API models."""

    def __init__(
        self,
        client: ShodanProvider | None = None,
        cache: dict[str, tuple[float, HostData]] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client or ShodanClient()
        self.cache = _host_cache if cache is None else cache
        self.clock = clock

    def host(self, ip: str) -> HostData:
        cached = self.cache.get(ip)
        if cached and cached[0] > self.clock():
            logger.info("network_recon query succeeded feature=host target=%s source=cache", ip)
            return cached[1]

        try:
            data = self._shape_host(self.client.host(ip))
        except Exception:
            logger.warning("network_recon query failed feature=host target=%s", ip, exc_info=True)
            raise
        self.cache[ip] = (self.clock() + HOST_CACHE_TTL_SECONDS, data)
        logger.info("network_recon query succeeded feature=host target=%s source=shodan", ip)
        return data

    def search(self, query: str, page: int) -> SearchData:
        try:
            raw = self.client.search(query, page)
            results = [self._shape_search_host(match) for match in raw.get("matches", [])[:20]]
        except Exception:
            logger.warning("network_recon query failed feature=search target=%s", query, exc_info=True)
            raise
        logger.info("network_recon query succeeded feature=search target=%s", query)
        return SearchData(total=int(raw.get("total", 0)), page=page, results=results)

    @classmethod
    def _shape_host(cls, raw: dict[str, Any]) -> HostData:
        services = [
            ServiceBanner(
                port=entry.get("port"), transport=entry.get("transport"),
                product=entry.get("product"), version=entry.get("version"), banner=entry.get("data"),
            )
            for entry in raw.get("data", [])
        ]
        ports = raw.get("ports") or [entry.port for entry in services if entry.port is not None]
        return HostData(
            ip=str(raw.get("ip_str", "")), open_ports=sorted({int(port) for port in ports}),
            services=services, org=raw.get("org"), isp=raw.get("isp"),
            location=cls._shape_location(raw.get("location", {})), os_guess=raw.get("os"),
            last_updated=raw.get("last_update"),
        )

    @classmethod
    def _shape_search_host(cls, raw: dict[str, Any]) -> SearchHost:
        return SearchHost(
            ip=str(raw.get("ip_str", "")), port=raw.get("port"), org=raw.get("org"),
            location=cls._shape_location(raw.get("location", {})),
        )

    @staticmethod
    def _shape_location(raw: dict[str, Any] | None) -> Location:
        raw = raw or {}
        return Location(
            country_name=raw.get("country_name"), city=raw.get("city"),
            latitude=raw.get("latitude"), longitude=raw.get("longitude"),
        )
