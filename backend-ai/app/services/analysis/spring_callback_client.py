import json
import os
from typing import Any
from urllib import request
from uuid import UUID


class SpringCallbackError(RuntimeError):
    pass


def send_scan_results(scan_id: UUID, payload: dict[str, Any]) -> None:
    base_url = os.getenv("SPRING_BOOT_BASE_URL", "http://localhost:8080").rstrip("/")
    internal_api_key = os.getenv("INTERNAL_API_KEY", "change-me-internal-api-key")
    url = f"{base_url}/internal/scans/{scan_id}/results"

    body = json.dumps(payload).encode("utf-8")
    callback_request = request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {internal_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(callback_request, timeout=15) as response:
            if response.status >= 400:
                raise SpringCallbackError(f"Spring callback failed with status {response.status}.")
    except OSError as exception:
        raise SpringCallbackError("Spring callback request failed.") from exception
