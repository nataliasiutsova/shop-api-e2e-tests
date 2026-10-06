import json
import logging

import allure
import requests

from utils.logging_utils import mask, truncate

logger = logging.getLogger("api")


class RequestClient:
    BASE_URL = "https://aqa-proka4.org/sandbox/api"

    def __init__(self, token: str | None = None, timeout: float = 30.0):
        self.session = requests.Session()
        self.timeout = timeout
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def get(self, path, *, allow_error=False, **kw):
        return self._request("GET", path, allow_error=allow_error, **kw)

    def post(self, path, *, allow_error=False, **kw):
        return self._request("POST", path, allow_error=allow_error, **kw)

    def put(self, path, *, allow_error=False, **kw):
        return self._request("PUT", path, allow_error=allow_error, **kw)

    def delete(self, path, *, allow_error=False, **kw):
        return self._request("DELETE", path, allow_error=allow_error, **kw)

    def _request(self, method, path, *, allow_error=False, **kw):
        url = f"{self.BASE_URL}/{path.lstrip('/')}"

        response = self.session.request(method, url, timeout=self.timeout, **kw)

        # LOG+ALLURE
        with allure.step(f"{method.upper()} {url} → {response.status_code}"):
            self._log_request(method, url, kw)
            self._log_response_status(response)
            self._log_response_body(response)

        # ERROR HANDLING
        if not allow_error and not (200 <= response.status_code < 400):
            raise AssertionError(
                f"HTTP {response.status_code} {method.upper()} {url}\n"
                f"{truncate(response.text, 500)}"
            )

        return response

    def _log_request(self, method, url, kw):

        # Console log
        logger.info("➡️  %s %s", method.upper(), url)

        params = kw.get("params")
        json_body = kw.get("json")
        data_body = kw.get("data")

        if params:
            logger.info("   params: %s", params)

        if json_body is not None:
            masked_body = mask(json_body)
            logger.info("   body (json): %s", masked_body)

        if data_body is not None and json_body is None:
            logger.info("   body (data): %s", truncate(str(data_body), 500))

        # Allure attach
        lines = [f"{method.upper()} {url}"]

        if params:
            lines.append("")
            lines.append("Query params:")
            lines.append(json.dumps(params, ensure_ascii=False, indent=2))

        if json_body is not None:
            lines.append("")
            lines.append("Body (json):")
            lines.append(json.dumps(mask(json_body), ensure_ascii=False, indent=2))

        allure.attach(
            "\n".join(lines),
            name="Request",
            attachment_type=allure.attachment_type.TEXT,
        )

    def _log_response_status(self, response):
        # Logs the response status to console and attaches it to Allure

        elapsed_ms = response.elapsed.total_seconds() * 1000
        summary = f"{response.status_code} {response.url} ({elapsed_ms:.0f} ms)"

        logger.info("⬅️  %s", summary)
        allure.attach(
            summary,
            name="Response status",
            attachment_type=allure.attachment_type.TEXT,
        )

    def _log_response_body(self, response):
        # Logs the response body to console and attaches it to Allure
        if not response.content:
            logger.info("   response body: <empty>")
            allure.attach(
                "<empty body>",
                name="Response body",
                attachment_type=allure.attachment_type.TEXT,
            )
            return

        try:
            data = response.json()
            masked = mask(data)
            logger.info("   response body: %s", masked)
            allure.attach(
                json.dumps(masked, ensure_ascii=False, indent=2),
                name="Response body",
                attachment_type=allure.attachment_type.JSON,
            )
            return
        except json.JSONDecodeError:
            pass

        truncated = truncate(response.text)
        logger.info("   response body (non-json): %s", truncated)
        allure.attach(
            truncated,
            name="Response body (non-JSON)",
            attachment_type=allure.attachment_type.TEXT,
        )
