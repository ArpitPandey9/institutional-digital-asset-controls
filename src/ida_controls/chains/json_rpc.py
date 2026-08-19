"""Minimal Ethereum-compatible JSON-RPC client."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def rpc_call(rpc_url: str, method: str, params: list | None = None):
    """Call one Ethereum JSON-RPC method and return its result."""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or [],
    }

    request = Request(
        rpc_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "institutional-digital-asset-controls/0.1",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"RPC HTTP error {exc.code}: {error_body[:500]}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"RPC connection error: {exc.reason}"
        ) from exc

    if "error" in body:
        raise RuntimeError(f"RPC error: {body['error']}")

    if "result" not in body:
        raise RuntimeError(f"Malformed RPC response: {body}")

    return body["result"]
