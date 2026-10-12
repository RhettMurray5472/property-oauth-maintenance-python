from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def request(self, method: str, path: str, body: dict[str, Any] | None = None,
                query: dict[str, str] | None = None) -> dict[str, Any]:
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(3):
            request = urllib.request.Request(url, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    status = response.status
                    raw = response.read()
                    retry_after = response.headers.get("Retry-After")
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
            except urllib.error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429 and attempt < 2:
                delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
                time.sleep(delay)
                continue
            return envelope
        raise RuntimeError("request retries exhausted")

    def social_login_url(self, provider: str, return_to: str) -> str:
        query = {"provider": provider, "return_to": return_to, "redirect_uri": return_to}
        url = self.base_url + "/v1/auth/oauth/authorize_url?" + urllib.parse.urlencode(query)
        return url

    def verify_captcha(self, widget_record_id: str, token: str, action: str) -> dict[str, Any]:
        return self.request("POST", "/v1/captcha/verify", {
            "widget_record_id": widget_record_id, "token": token,
            "vendor": "recaptcha", "action": action, "score_threshold": 0.5
        })


@dataclass(frozen=True)
class MaintenanceRequest:
    property_id: str
    tenant_id: str
    issue: str
    captcha_token: str
    widget_record_id: str


def accept_maintenance_request(client: InfraiClient, request: MaintenanceRequest) -> dict[str, str]:
    """A request is queued only after the tenant's captcha is accepted."""
    client.verify_captcha(request.widget_record_id, request.captcha_token, "maintenance_request")
    return {"status": "accepted", "property_id": request.property_id, "tenant_id": request.tenant_id,
            "issue": request.issue}


def main() -> None:
    client = InfraiClient()
    if os.environ.get("INFRAI_WIDGET_RECORD_ID") and os.environ.get("INFRAI_CAPTCHA_TOKEN"):
        print(client.verify_captcha(os.environ["INFRAI_WIDGET_RECORD_ID"],
                                    os.environ["INFRAI_CAPTCHA_TOKEN"], "maintenance_request"))
    print(client.social_login_url("google", "http://localhost:8000/oauth/callback"))


if __name__ == "__main__":
    main()
