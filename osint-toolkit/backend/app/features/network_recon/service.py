"""Provider-agnostic network reconnaissance orchestration and TTL caching."""

from collections.abc import Callable
import ipaddress
import time
from typing import Any, Protocol

import dns.exception
import dns.resolver

from app.core.config import get_settings
from app.core.exceptions import LookupNotFoundError, LookupProviderError, LookupTimeoutError
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
        resolve_hostname: Callable[[str], str] | None = None,
    ) -> None:
        self.client = client or ShodanClient()
        self.cache = _host_cache if cache is None else cache
        self.clock = clock
        self.resolve_hostname = resolve_hostname or self._resolve_hostname

    def host(self, target: str) -> HostData:
        """Look up an IP directly, or resolve a DNS hostname before querying Shodan."""
        ip = self._resolve_target(target)
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

    def _resolve_target(self, target: str) -> str:
        try:
            return str(ipaddress.ip_address(target))
        except ValueError:
            return self.resolve_hostname(target)

    @staticmethod
    def _resolve_hostname(hostname: str) -> str:
        settings = get_settings()
        resolver = dns.resolver.Resolver()
        resolver.timeout = settings.dns_timeout_seconds
        resolver.lifetime = settings.dns_lifetime_seconds
        try:
            answers = resolver.resolve(hostname, "A")
            return str(answers[0])
        except dns.resolver.NoAnswer:
            try:
                answers = resolver.resolve(hostname, "AAAA")
                return str(answers[0])
            except dns.resolver.NoAnswer as exc:
                raise LookupNotFoundError("Hostname has no IP address records") from exc
            except dns.resolver.NXDOMAIN as exc:
                raise LookupNotFoundError("Hostname does not resolve") from exc
            except dns.exception.Timeout as exc:
                raise LookupTimeoutError("DNS lookup timed out") from exc
            except dns.exception.DNSException as exc:
                raise LookupProviderError("DNS lookup failed") from exc
        except dns.resolver.NXDOMAIN as exc:
            raise LookupNotFoundError("Hostname does not resolve") from exc
        except dns.exception.Timeout as exc:
            raise LookupTimeoutError("DNS lookup timed out") from exc
        except dns.exception.DNSException as exc:
            raise LookupProviderError("DNS lookup failed") from exc

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
