"""Thin, replaceable wrappers around third-party WHOIS and DNS libraries."""

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import dns.exception
import dns.resolver
import whois

from app.core.config import get_settings
from app.core.exceptions import LookupNotFoundError, LookupProviderError, LookupTimeoutError
from app.features.domain_intel.schemas import DnsData, WhoisData


class DomainIntelClient:
    """Adapter that keeps provider-specific APIs out of the service layer."""

    def fetch_whois(self, domain: str) -> WhoisData:
        try:
            record: Any = whois.whois(domain)
        except TimeoutError as exc:
            raise LookupTimeoutError("WHOIS lookup timed out") from exc
        except Exception as exc:
            if "not found" in str(exc).lower() or "no match" in str(exc).lower():
                raise LookupNotFoundError("Domain was not found in WHOIS records") from exc
            raise LookupProviderError("WHOIS lookup failed") from exc

        if not record or not getattr(record, "domain_name", None):
            raise LookupNotFoundError("Domain was not found in WHOIS records")

        return WhoisData(
            registrar=self._as_string(getattr(record, "registrar", None)),
            creation_date=self._as_date(getattr(record, "creation_date", None)),
            expiration_date=self._as_date(getattr(record, "expiration_date", None)),
            name_servers=self._as_strings(getattr(record, "name_servers", None)),
            registrant_org=self._as_string(getattr(record, "org", None)),
        )

    def fetch_dns(self, domain: str) -> DnsData:
        settings = get_settings()
        resolver = dns.resolver.Resolver()
        resolver.timeout = settings.dns_timeout_seconds
        resolver.lifetime = settings.dns_lifetime_seconds
        try:
            return DnsData(
                a=self._resolve(resolver, domain, "A"),
                aaaa=self._resolve(resolver, domain, "AAAA"),
                mx=self._resolve(resolver, domain, "MX"),
                ns=self._resolve(resolver, domain, "NS"),
                txt=self._resolve(resolver, domain, "TXT"),
            )
        except dns.resolver.NXDOMAIN as exc:
            raise LookupNotFoundError("Domain does not resolve") from exc
        except dns.exception.Timeout as exc:
            raise LookupTimeoutError("DNS lookup timed out") from exc
        except dns.exception.DNSException as exc:
            raise LookupProviderError("DNS lookup failed") from exc

    @staticmethod
    def _resolve(resolver: dns.resolver.Resolver, domain: str, record_type: str) -> list[str]:
        try:
            return [answer.to_text().rstrip(".") for answer in resolver.resolve(domain, record_type)]
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return []

    @staticmethod
    def _as_string(value: Any) -> str | None:
        if isinstance(value, (list, tuple)):
            value = value[0] if value else None
        return str(value) if value is not None else None

    @classmethod
    def _as_strings(cls, value: Any) -> list[str]:
        if value is None:
            return []
        values: Iterable[Any] = value if isinstance(value, (list, tuple, set)) else [value]
        return sorted({str(item).lower().rstrip(".") for item in values})

    @staticmethod
    def _as_date(value: Any) -> datetime | None:
        if isinstance(value, (list, tuple)):
            value = value[0] if value else None
        return value if isinstance(value, datetime) else None
