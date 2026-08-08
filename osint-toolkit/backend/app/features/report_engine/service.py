"""Concurrent in-process orchestration, aggregation, and temporary report caching."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any, Protocol
from uuid import uuid4

from app.core.logging import get_logger
from app.features.breach_check.service import BreachCheckService
from app.features.domain_intel.service import DomainIntelService
from app.features.network_recon.service import NetworkReconService
from app.features.report_engine.aggregator import aggregate_report, make_section
from app.features.report_engine.schemas import InvestigationReport, ModuleName, ReportRequest, ReportSection, ReportTarget
from app.features.social_profiling.service import SocialProfilingService


logger = get_logger(__name__)
REPORT_CACHE_TTL_SECONDS = 1800.0


class DomainService(Protocol):
    def whois(self, domain: str) -> Any: ...
    def dns(self, domain: str) -> Any: ...


class NetworkService(Protocol):
    def host(self, ip: str) -> Any: ...


class SocialService(Protocol):
    async def username(self, value: str) -> Any: ...


class BreachService(Protocol):
    async def email(self, value: str) -> Any: ...


@dataclass
class CachedReport:
    expires_at: float
    report: InvestigationReport
    html: str


_report_cache: dict[str, CachedReport] = {}


class ReportEngineService:
    """Call feature services directly and keep individual module failures isolated."""

    def __init__(
        self,
        domain_service: DomainService | None = None,
        network_service: NetworkService | None = None,
        social_service: SocialService | None = None,
        breach_service: BreachService | None = None,
        cache: dict[str, CachedReport] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.domain_service = domain_service or DomainIntelService()
        self.network_service = network_service or NetworkReconService()
        self.social_service = social_service or SocialProfilingService()
        self.breach_service = breach_service or BreachCheckService()
        self.cache = _report_cache if cache is None else cache
        self.clock = clock

    async def generate(self, request: ReportRequest) -> InvestigationReport:
        """Run applicable requested modules concurrently and return a normalized report."""
        target = ReportTarget(domain=request.domain, email=request.email, username=request.username, ip=str(request.ip) if request.ip else None)
        tasks = [self._run_module(module, request) for module in request.modules]
        sections = list(await asyncio.gather(*tasks))
        report = aggregate_report(str(uuid4()), target, request.modules, sections)
        logger.info("report_engine generated report_id=%s modules=%s", report.report_id, len(request.modules))
        return report

    def cache_report(self, report: InvestigationReport, html: str) -> None:
        self._purge_expired()
        self.cache[report.report_id] = CachedReport(self.clock() + REPORT_CACHE_TTL_SECONDS, report, html)

    def take_preview(self, report_id: str) -> CachedReport | None:
        self._purge_expired()
        # Preview is intentionally one-time in this prototype to minimise retention.
        return self.cache.pop(report_id, None)

    async def _run_module(self, module: ModuleName, request: ReportRequest) -> ReportSection:
        if module == "domain_intel":
            if not request.domain:
                return make_section(module, "skipped")
            try:
                whois, dns = await asyncio.gather(
                    asyncio.to_thread(self.domain_service.whois, request.domain),
                    asyncio.to_thread(self.domain_service.dns, request.domain),
                )
                data = {"whois": whois.model_dump(mode="json"), "dns": dns.model_dump(mode="json")}
                return make_section(module, "empty" if not any(data["dns"].values()) else "complete", data)
            except Exception:
                logger.warning("report_engine module failed module=%s", module, exc_info=True)
                return make_section(module, "unavailable", error="Domain intelligence was temporarily unavailable.")
        if module == "network_recon":
            if not request.ip:
                return make_section(module, "skipped")
            try:
                host = await asyncio.to_thread(self.network_service.host, str(request.ip))
                data = host.model_dump(mode="json")
                return make_section(module, "empty" if not data.get("open_ports") else "complete", data)
            except Exception:
                logger.warning("report_engine module failed module=%s", module, exc_info=True)
                return make_section(module, "unavailable", error="Network reconnaissance was temporarily unavailable.")
        if module == "social_profiling":
            if not request.username:
                return make_section(module, "skipped")
            try:
                result = await self.social_service.username(request.username)
                data = result.model_dump(mode="json")
                return make_section(module, "empty" if not any(item["status"] == "found" for item in data["results"]) else "complete", data)
            except Exception:
                logger.warning("report_engine module failed module=%s", module, exc_info=True)
                return make_section(module, "unavailable", error="Social profiling was temporarily unavailable.")
        if not request.email:
            return make_section(module, "skipped")
        try:
            result = await self.breach_service.email(request.email)
            data = result.model_dump(mode="json")
            return make_section(module, "complete" if data["breached"] else "empty", data)
        except Exception:
            logger.warning("report_engine module failed module=%s", module, exc_info=True)
            return make_section(module, "unavailable", error="Breach data was temporarily unavailable.")

    def _purge_expired(self) -> None:
        now = self.clock()
        for report_id, cached in list(self.cache.items()):
            if cached.expires_at <= now:
                del self.cache[report_id]
