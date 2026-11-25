"""Base scraper class for Proballers website.

Inherits session management, output paths, data persistence, and text
cleaning from ``WebScraperBase``.  Adds Proballers-specific rate limiting,
URL building, and a convenience ``_fetch_page`` that returns parsed HTML.
"""

from __future__ import annotations

import random
import re
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse, urlsplit

import requests

from ..web_scraper_base import WebScraperBase
from .config import (
    BASE_URL,
    MAX_RETRIES,
    RAW_DATA_DIR,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF_FACTOR,
    ROBOTS_DISALLOWED_PATTERNS,
    USER_AGENT,
    USER_AGENTS,
)

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup


class ProballersScrapeDisabledError(RuntimeError):
    """Outbound collection from proballers.com is switched off.

    ``ENABLE_PROBALLERS_SCRAPE`` defaults to OFF (ATI-2956): their Legal
    Notice requires written authorisation, the site has answered 403 to every
    automated fetch since January 2026, and on 2026-09-03 they were told in
    writing that automated collection has stopped. Raised, not logged, for the
    same reason as :class:`RobotsDisallowedError` -- a fetch that silently
    returns nothing reads exactly like a page that had nothing on it.
    """


class RobotsDisallowedError(RuntimeError):
    """A URL was built for a path proballers.com/robots.txt disallows.

    Raised rather than logged: a crawl that silently skips a disallowed page
    looks identical to one that never wanted it, and "we thought the guard was
    on" is not a defence anybody can check afterwards.
    """


class UnapprovedProballersURL(ValueError):
    """A request or redirect would leave the approved HTTPS origin."""


def _validate_proballers_url(url: str) -> str:
    """Accept only the exact Proballers HTTPS host with no unusual authority."""
    # Backslashes and control characters can be parsed differently by clients.
    if any(ord(char) <= 32 or ord(char) == 127 for char in url) or chr(92) in url:
        raise UnapprovedProballersURL("Invalid characters in Proballers URL")
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc.lower() not in {
        "www.proballers.com",
        "www.proballers.com:443",
    }:
        raise UnapprovedProballersURL(
            "Proballers requests require HTTPS to www.proballers.com"
        )
    return url


def request_approved_proballers_url(
    url: str,
    request_get: Callable[..., requests.Response],
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    """Make only approved Proballers requests, validating each redirect first."""
    current = url
    for redirects in range(6):
        _validate_proballers_url(current)
        _refuse_if_robots_disallowed(urlsplit(current).path or "/")
        kwargs: dict[str, Any] = {"timeout": timeout, "allow_redirects": False}
        if headers is not None:
            kwargs["headers"] = headers
        response = request_get(current, **kwargs)
        if response.status_code not in {301, 302, 303, 307, 308}:
            return response
        if redirects == 5:
            raise UnapprovedProballersURL("Proballers redirect limit exceeded")
        location = response.headers.get("Location")
        if not location:
            raise UnapprovedProballersURL("Proballers redirect has no Location")
        current = urljoin(current, location)
    raise AssertionError("unreachable redirect loop")


def _robots_pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a robots.txt path pattern, where ``*`` is the only wildcard.

    robots.txt globbing is not fnmatch: ``*`` matches any sequence including
    ``/``, and a pattern is a *prefix* match on the path unless it ends in
    ``$``. Every other character is literal, so the rest is escaped.
    """
    body = "".join(
        ".*" if part == "*" else re.escape(part) for part in re.split(r"(\*)", pattern)
    )
    return re.compile("^" + body)


_ROBOTS_DISALLOWED_RE = tuple(
    (pattern, _robots_pattern_to_regex(pattern))
    for pattern in ROBOTS_DISALLOWED_PATTERNS
)


def _refuse_if_robots_disallowed(path: str) -> None:
    """Refuse a path disallowed for ``User-agent: *`` (ATI-2793).

    Applied at URL construction, which is the one funnel every scraper in this
    package goes through — a per-call-site check would miss whichever site a
    future feature adds.
    """
    probe = path
    if probe.startswith("http"):
        probe = urlparse(probe).path or "/"
    for pattern, rx in _ROBOTS_DISALLOWED_RE:
        if rx.match(probe):
            raise RobotsDisallowedError(
                f"proballers.com/robots.txt disallows {pattern!r} for "
                f"User-agent: * — refusing to build a URL for {path!r}. "
                "If this path is genuinely needed, the robots directive has to "
                "change first (or written permission obtained), not this guard."
            )


class ProballersBaseScraper(WebScraperBase):
    """Base class for Proballers web scrapers.

    Provides common functionality for scraping data from proballers.com
    using BeautifulSoup for HTML parsing.

    Args:
        data_dir: Directory to save data. Defaults to data/raw/proballers/.

    """

    source_name = "proballers"
    user_agents = USER_AGENTS
    max_retries = MAX_RETRIES
    backoff_factor = RETRY_BACKOFF_FACTOR
    request_timeout = REQUEST_TIMEOUT

    def __init__(self, data_dir: Path = RAW_DATA_DIR) -> None:
        super().__init__(data_dir)

    def _create_session(self) -> requests.Session:
        """A plain session — proballers needs no Cloudflare-evasion transport.

        ``WebScraperBase`` builds a ``cloudscraper`` session configured with
        ``browser={"browser": "chrome", ...}``. Measured 2026-08-18, a plain
        ``requests`` session carrying :data:`USER_AGENT` returns 200 on all four
        path shapes this scraper requests -- landing, schedule, game and player
        (639 KB, 93 KB and 250 KB of real content respectively). The browser
        spoofing was never what got us served.

        Overridden here rather than in the base class: realgm and
        basketball_reference share that base, and RealGM does 403 us
        (ATI-2794), so whether they still need it is a separate question with
        its own evidence. See ATI-2866.
        """
        session = requests.Session()
        session.headers.update(self._initial_headers())
        return session

    def _initial_headers(self) -> dict[str, str]:
        """Identify the scraper, plus the two headers proballers wants.

        ``User-Agent`` is set HERE and not inherited. The base class sets it in
        its own ``_initial_headers``, and this override used to drop the key
        entirely -- which made :data:`USER_AGENTS` dead config for this scraper
        and let cloudscraper's spoofed Chrome UA go out on the wire instead
        (ATI-2866). ``test_the_session_actually_sends_the_honest_user_agent``
        reads the header off a constructed session so that cannot recur.
        """
        return {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "DNT": "1",
        }

    def _rate_limit(self) -> None:
        """Random delay between requests, skipping the first."""
        if self._request_count > 0:
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            self.logger.debug("Rate limiting: waiting %.1fs", delay)
            time.sleep(delay)

    def _fetch_html(self, url: str) -> str | None:
        _validate_proballers_url(url)
        return super()._fetch_html(url)

    def _request_url(self, url: str) -> requests.Response:
        """Follow at most five redirects, validating each destination first."""
        return request_approved_proballers_url(
            url, self.session.get, timeout=self.request_timeout
        )

    def _fetch_page(self, url: str) -> BeautifulSoup | None:
        """Fetch a page and return parsed BeautifulSoup.

        Parameters
        ----------
        url : str
            URL to fetch.

        Returns
        -------
        BeautifulSoup | None
            Parsed HTML, or ``None`` if the fetch failed.

        """
        from src.config.features import get_flag

        if not get_flag("ENABLE_PROBALLERS_SCRAPE"):
            raise ProballersScrapeDisabledError(
                "Proballers collection is disabled (ENABLE_PROBALLERS_SCRAPE=0, "
                "ATI-2956); refusing to fetch " + url
            )
        html = self._fetch_html(url)
        if html is None:
            return None
        return self._parse_html(html)

    def build_url(self, path: str) -> str:
        """Build full URL from relative path.

        Args:
            path: Relative path (e.g., '/basketball/league/acb/games/2024').

        Returns:
            Full URL.

        Raises:
            RobotsDisallowedError: if the path is one proballers.com/robots.txt
                disallows for the generic ``User-agent: *`` group.

        """
        url = _validate_proballers_url(urljoin(f"{BASE_URL}/", path))
        _refuse_if_robots_disallowed(urlsplit(url).path or "/")
        return url

    def __enter__(self) -> ProballersBaseScraper:  # type: ignore[override]
        return self
