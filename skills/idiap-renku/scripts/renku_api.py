#!/usr/bin/env python3
"""Minimal Renku 2.0 API client: device-flow login, token refresh, raw JSON calls.

Usage:
    renku_api.py login                         # interactive (browser) device login
    renku_api.py logout                        # forget cached tokens
    renku_api.py token                         # print a valid access token
    renku_api.py GET /user                     # call /api/data/user
    renku_api.py POST /projects '{"name": ...}'
    renku_api.py PATCH /projects/<id> @body.json --if-match <etag>
    renku_api.py --selftest

Environment:
    RENKU_URL        instance base URL (default: https://renku.idiap.ch)
    RENKU_TOKEN_FILE token cache (default: ~/.cache/renku-api/<host>.json)

Only the standard library is used, so it runs anywhere ``python3`` exists.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from pathlib import Path

RENKU_URL = os.environ.get("RENKU_URL", "https://renku.idiap.ch").rstrip("/")
CLIENT_ID = "renku-cli"  # public Keycloak client also used by the official `rnk` CLI
OIDC = f"{RENKU_URL}/auth/realms/Renku/protocol/openid-connect"
TOKEN_FILE = Path(
    os.environ.get(
        "RENKU_TOKEN_FILE",
        Path.home()
        / ".cache"
        / "renku-api"
        / f"{urllib.parse.urlparse(RENKU_URL).hostname}.json",
    )
)
SKEW = 30  # seconds of margin before considering a token expired


def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    with urllib.request.urlopen(urllib.request.Request(url, body)) as r:
        return json.load(r)


def _save(tok: dict) -> dict:
    now = time.time()
    tok["expires_at"] = now + tok.get("expires_in", 0)
    if "refresh_expires_in" in tok:
        # 0 means "no expiry" (offline tokens) in Keycloak
        r = tok["refresh_expires_in"]
        tok["refresh_expires_at"] = now + r if r else float("inf")
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.touch(mode=0o600, exist_ok=True)
    TOKEN_FILE.chmod(0o600)
    TOKEN_FILE.write_text(json.dumps(tok))
    return tok


def needs(tok: dict | None, now: float) -> str:
    """Decide what to do with a cached token: 'use', 'refresh' or 'login'."""
    if not tok:
        return "login"
    if tok.get("expires_at", 0) - SKEW > now:
        return "use"
    if tok.get("refresh_token") and tok.get("refresh_expires_at", 0) - SKEW > now:
        return "refresh"
    return "login"


def login() -> None:
    d = _post_form(f"{OIDC}/auth/device", {"client_id": CLIENT_ID, "scope": "openid"})
    print(
        f"Open {d['verification_uri_complete']}\n(or {d['verification_uri']} and "
        f"enter code {d['user_code']}); waiting up to {d['expires_in']}s...",
        file=sys.stderr,
        flush=True,
    )
    interval, deadline = d.get("interval", 5), time.time() + d["expires_in"]
    while time.time() < deadline:
        time.sleep(interval)
        try:
            tok = _post_form(
                f"{OIDC}/token",
                {
                    "client_id": CLIENT_ID,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": d["device_code"],
                },
            )
        except urllib.error.HTTPError as e:
            err = json.loads(e.read() or b"{}").get("error")
            if err == "authorization_pending":
                continue
            if err == "slow_down":
                interval += 5
                continue
            sys.exit(f"login failed: {err}")
        _save(tok)
        print(f"Logged in; token cached at {TOKEN_FILE}", file=sys.stderr)
        return
    sys.exit("login timed out")


def access_token() -> str:
    tok = json.loads(TOKEN_FILE.read_text()) if TOKEN_FILE.exists() else None
    action = needs(tok, time.time())
    if action == "refresh":
        try:
            tok = _save(
                _post_form(
                    f"{OIDC}/token",
                    {
                        "client_id": CLIENT_ID,
                        "grant_type": "refresh_token",
                        "refresh_token": tok["refresh_token"],
                    },
                )
            )
        except urllib.error.HTTPError:
            action = "login"
    if action == "login":
        sys.exit("not logged in (or session expired): run `renku_api.py login`")
    return tok["access_token"]


def call(method: str, path: str, body: str | None, if_match: str | None) -> int:
    url = f"{RENKU_URL}/api/data/{path.lstrip('/')}"
    if body and body.startswith("@"):
        body = Path(body[1:]).read_text()
    req = urllib.request.Request(
        url, data=body.encode() if body else None, method=method.upper()
    )
    req.add_header("Authorization", f"Bearer {access_token()}")
    req.add_header("Accept", "application/json")
    if body:
        req.add_header("Content-Type", "application/json")
    if if_match:
        req.add_header("If-Match", if_match)
    try:
        with urllib.request.urlopen(req) as r:
            status, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, raw = e.code, e.read()
    text = raw.decode(errors="replace")
    try:
        text = json.dumps(json.loads(text), indent=2)
    except ValueError:
        pass
    if text:
        print(text)
    if status >= 400:
        print(f"HTTP {status} {method.upper()} {url}", file=sys.stderr)
        return 1
    return 0


def selftest() -> None:
    now = 1000.0
    assert needs(None, now) == "login"
    assert needs({"expires_at": now + 300}, now) == "use"
    assert needs({"expires_at": now + 10}, now) != "use"  # within skew
    stale = {"expires_at": now - 1, "refresh_token": "r"}
    assert needs({**stale, "refresh_expires_at": now + 600}, now) == "refresh"
    assert needs({**stale, "refresh_expires_at": now - 1}, now) == "login"
    assert needs({**stale, "refresh_expires_at": float("inf")}, now) == "refresh"
    assert needs({"expires_at": now - 1}, now) == "login"
    print("selftest ok")


def main(argv: list[str]) -> int:
    if_match = None
    if "--if-match" in argv:
        i = argv.index("--if-match")
        if_match = argv[i + 1]
        del argv[i : i + 2]
    match argv:
        case ["--selftest"]:
            selftest()
        case ["login"]:
            login()
        case ["logout"]:
            TOKEN_FILE.unlink(missing_ok=True)
        case ["token"]:
            print(access_token())
        case [method, path] | [method, path, _] if method.upper() in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }:
            return call(method, path, argv[2] if len(argv) > 2 else None, if_match)
        case _:
            print(__doc__, file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
