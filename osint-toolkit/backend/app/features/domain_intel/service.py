"""Business orchestration and audit logging for domain intelligence."""

from app.core.logging import get_logger
from app.features.domain_intel.client import DomainIntelClient
from app.features.domain_intel.schemas import DnsData, WhoisData


logger = get_logger(__name__)


class DomainIntelService:
    """Coordinates domain lookup clients without HTTP-specific concerns."""

    def __init__(self, client: DomainIntelClient | None = None) -> None:
        self.client = client or DomainIntelClient()

    def whois(self, domain: str) -> WhoisData:
        try:
            result = self.client.fetch_whois(domain)
        except Exception:
            logger.warning("domain_intel query failed feature=whois domain=%s", domain, exc_info=True)
            raise
        logger.info("domain_intel query succeeded feature=whois domain=%s", domain)
        return result

    def dns(self, domain: str) -> DnsData:
        try:
            result = self.client.fetch_dns(domain)
        except Exception:
            logger.warning("domain_intel query failed feature=dns domain=%s", domain, exc_info=True)
            raise
        logger.info("domain_intel query succeeded feature=dns domain=%s", domain)
        return result
