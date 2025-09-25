from __future__ import annotations

import json
import os
import ssl
import sys
import time
from urllib import error, request

import pytest
import truststore


def _truthy_env(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return False
    value = raw.strip().lower()
    return value not in {"", "0", "false", "no"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@pytest.mark.skipif(
    sys.platform != "win32", reason="Windows trust store only available on Windows"
)
def test_win_ca_smoke() -> None:
    if not _truthy_env("WIN_CA_SMOKE"):
        pytest.skip("WIN_CA_SMOKE not set; skipping Windows CA smoke test")

    url = os.environ.get("SMOKE_URL", "https://localhost:4443/")
    attempts = _env_int("SMOKE_ATTEMPTS", 60)
    delay_ms = _env_int("SMOKE_DELAY_MS", 500)

    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = True

    last_error: Exception | None = None

    for _ in range(attempts):
        try:
            with request.urlopen(url, context=ctx, timeout=30) as response:
                status = response.getcode()
                body = json.loads(response.read().decode("utf-8", errors="replace"))
                assert status == 200, f"unexpected status {status} from {url}"
                assert body["status"] == "ok", f"unexpected response body {body!r} from {url}"
                return
        except error.URLError as exc:  # handshake failure before trust
            last_error = exc
        except Exception as exc:  # pragma: no cover - defensive catch
            last_error = exc
        time.sleep(max(delay_ms, 0) / 1000.0)

    detail = repr(last_error) if last_error else "no response received"
    pytest.fail(f"failed to reach {url} within {attempts} attempts: {detail}")
