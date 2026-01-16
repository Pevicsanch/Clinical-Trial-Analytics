"""API client for ClinicalTrials.gov API v2.

Handles pagination, rate limiting, and error handling for data extraction.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import requests
from loguru import logger

from src.config.settings import settings


class ClinicalTrialsAPI:
    """Client for ClinicalTrials.gov API v2."""

    def __init__(
        self,
        base_url: str | None = None,
        page_size: int | None = None,
        timeout: int | None = None,
    ):
        """Initialize API client.

        Args:
            base_url: API base URL. Defaults to settings.api_base_url.
            page_size: Number of records per page. Defaults to settings.api_page_size.
            timeout: Request timeout in seconds. Defaults to settings.api_timeout.
        """
        self.base_url = base_url or settings.api_base_url
        self.page_size = page_size or settings.api_page_size
        self.timeout = timeout or settings.api_timeout
        
        # Headers required by ClinicalTrials.gov API
        # Use a standard browser User-Agent to avoid blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://clinicaltrials.gov/",
            "Origin": "https://clinicaltrials.gov",
        }
        
        # Use requests.Session for cookie persistence (different TLS fingerprint than httpx)
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.timeout = self.timeout
        
        # Warm-up: visit homepage first to get cookies (like a browser)
        self._warm_up()

    def _warm_up(self) -> None:
        """Warm-up request to homepage to get cookies and establish session.
        
        This mimics browser behavior: visit homepage first, then API.
        Many WAFs require this to avoid blocking.
        """
        try:
            logger.debug("Warming up: visiting homepage to get cookies...")
            warm_up_headers = {
                "User-Agent": self.headers["User-Agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": self.headers["Accept-Language"],
            }
            self.session.get(
                "https://clinicaltrials.gov/",
                headers=warm_up_headers,
                timeout=self.timeout,
            )
            logger.debug("Warm-up successful: cookies obtained")
        except Exception as e:
            logger.warning(f"Warm-up failed (non-critical): {str(e)}")
            # Continue anyway - warm-up is best effort

    def _request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """Make HTTP request.

        Args:
            url: Request URL.
            params: Query parameters.

        Returns:
            JSON response as dictionary.

        Raises:
            requests.RequestException: If request fails.
        """
        try:
            logger.debug(f"Request URL: {url}, Params: {params}")

            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            resp = e.response
            status_code = resp.status_code if resp is not None else None
            reason = getattr(resp, "reason", "") if resp is not None else ""

            # Helpful preview for debugging (avoid huge logs)
            content_type = (resp.headers.get("content-type", "").lower() if resp is not None else "")
            text_preview = (resp.text[:500] if resp is not None and hasattr(resp, "text") else "")

            # ------------------------------------------------------------
            # 403: WAF blocking — do NOT retry
            # ------------------------------------------------------------
            if status_code == 403:
                is_html = "text/html" in content_type or text_preview.strip().startswith("<")

                logger.error(f"API request blocked by WAF (403): {url}")
                logger.error(f"Request headers sent: {dict(getattr(e.request, 'headers', {}))}")
                logger.error(f"Response content-type: {content_type}")
                logger.error(f"Response preview: {text_preview}")

                if is_html:
                    logger.error(
                        "WAF returned an HTML challenge page. Likely causes:\n"
                        "  1) Cookie/session issue (warm-up may have failed)\n"
                        "  2) IP-based blocking\n"
                        "  3) WAF blocking this HTTP client fingerprint"
                    )
                else:
                    logger.error(
                        "WAF returned a JSON error. Likely causes:\n"
                        "  1) Invalid request parameters\n"
                        "  2) Rate limiting\n"
                        "  3) Server-side validation"
                    )
                raise

            # ------------------------------------------------------------
            # 400: often invalid/expired pageToken during deep pagination
            # Make this fail fast with a clear message (no attribute errors)
            # ------------------------------------------------------------
            if status_code == 400 and params.get("pageToken"):
                logger.warning(
                    "API returned 400 Bad Request with a pageToken. "
                    "This usually means the token became invalid/expired during deep pagination. "
                    "Consider lowering --max-records or restarting extraction."
                )
                logger.warning(f"URL: {url}")
                logger.warning(f"Params: {params}")
                logger.debug(f"Response preview: {text_preview}")
                raise

            # ------------------------------------------------------------
            # Retryable errors (caller may implement retry logic)
            # ------------------------------------------------------------
            if status_code in (429, 500, 502, 503, 504):
                logger.warning(f"API request failed with retryable error: {url} - {status_code} {reason}")
                raise

            # ------------------------------------------------------------
            # Other client errors
            # ------------------------------------------------------------
            logger.error(f"API request failed: {url} - {status_code} {reason}")
            logger.error(f"Request headers sent: {dict(getattr(e.request, 'headers', {}))}")
            logger.debug(f"Response content-type: {content_type}")
            logger.debug(f"Response preview: {text_preview}")
            raise

        except requests.RequestException as e:
            logger.error(f"API request failed: {url} - {str(e)}")
            raise

    def fetch_studies_page(
        self, page_token: str | None = None, page_size: int | None = None
    ) -> dict[str, Any]:
        """Fetch a single page of studies.

        Args:
            page_token: Token for pagination (None for first page).
            page_size: Number of records per page.

        Returns:
            API response with studies and next page token.
        """
        url = f"{self.base_url}/studies"
        params: dict[str, Any] = {
            "pageSize": page_size or self.page_size,
        }

        if page_token:
            params["pageToken"] = page_token

        logger.debug(f"Fetching page: {url} with params {params}")
        
        # Small delay before request to avoid rate limiting
        time.sleep(1.0)
        
        response = self._request(url, params)

        return response

    def fetch_all_studies(
        self, max_records: int | None = None
    ) -> Iterator[dict[str, Any]]:
        """Fetch all studies with pagination.

        Args:
            max_records: Maximum number of records to fetch.

        Yields:
            Study records from API.
        """
        max_records = max_records or settings.api_max_records
        page_token: str | None = None
        total_fetched = 0

        logger.info(f"Starting to fetch studies (max: {max_records})")

        while total_fetched < max_records:
            # Calculate how many records to fetch in this page
            remaining = max_records - total_fetched
            page_size = min(self.page_size, remaining)

            try:
                response = self.fetch_studies_page(page_token, page_size)
                studies = response.get("studies", [])

                if not studies:
                    logger.info("No more studies available")
                    break

                for study in studies:
                    yield study
                    total_fetched += 1

                    if total_fetched >= max_records:
                        break

                # Check for next page
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    logger.info("Reached last page")
                    break

                page_token = next_page_token
                logger.info(f"Fetched {total_fetched}/{max_records} studies")

                # Rate limiting: delay between requests to avoid 403
                time.sleep(2.0)

            except Exception as e:
                logger.error(f"Error fetching studies: {str(e)}")
                raise

        logger.info(f"Completed fetching {total_fetched} studies")

    def save_raw_data(
        self, output_dir: Path, max_records: int | None = None
    ) -> tuple[Path, Path]:
        """Fetch and save raw data to JSONL file.

        Args:
            output_dir: Directory to save raw data.
            max_records: Maximum number of records to fetch.

        Returns:
            Tuple of (data_file_path, metadata_file_path).
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_file = output_dir / f"studies_{timestamp}.jsonl"
        metadata_file = output_dir / f"metadata_{timestamp}.json"

        logger.info(f"Saving raw data to {data_file}")

        # Fetch and save studies
        total_saved = 0
        with open(data_file, "w", encoding="utf-8") as f:
            for study in self.fetch_all_studies(max_records):
                f.write(json.dumps(study) + "\n")
                total_saved += 1

        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "total_studies": total_saved,
            "page_size": self.page_size,
            "max_records": max_records or settings.api_max_records,
            "timeout": self.timeout,
            "api_base_url": self.base_url,
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved {total_saved} studies to {data_file}")
        logger.info(f"Metadata saved to {metadata_file}")

        return data_file, metadata_file

    def close(self):
        """Close HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
