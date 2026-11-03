"""Licence keys and the 30-day trial.

A key is ``ERISMA-<base32(payload)>.<base32(signature)>``; the payload is JSON
``{"name", "email", "plan", "expires"}`` (``expires`` = ISO date or "" for perpetual) signed with
the publisher's Ed25519 private key.  Only the public key is shipped, so keys cannot be forged.
State is kept in the user's profile (``%APPDATA%\\Erisma`` or ``~/.config/erisma``; override
with ``ERISMA_HOME``).
"""

from __future__ import annotations

import base64
import json
import os
from datetime import date, timedelta
from pathlib import Path

from . import ed25519

PUBLIC_KEY = bytes.fromhex("01dedde79432fb4b5019cea5b3d3d2cf460a285777235e10a5737594442f71e4")
TRIAL_DAYS = 30


def home() -> Path:
    env = os.environ.get("ERISMA_HOME")
    if env:
        return Path(env)
    base = os.environ.get("APPDATA") or os.path.join(Path.home(), ".config")
    return Path(base) / ("Erisma" if os.environ.get("APPDATA") else "erisma")


def _b32(b: bytes) -> str:
    return base64.b32encode(b).decode().rstrip("=")


def _unb32(s: str) -> bytes:
    s = s.strip().upper()
    return base64.b32decode(s + "=" * (-len(s) % 8))


def make_key(secret: bytes, name: str, email: str = "", plan: str = "pro",
             expires: str = "") -> str:
    payload = json.dumps({"name": name, "email": email, "plan": plan, "expires": expires},
                         separators=(",", ":"), ensure_ascii=False).encode()
    return f"ERISMA-{_b32(payload)}.{_b32(ed25519.sign(secret, payload))}"


def parse_key(key: str, public: bytes = PUBLIC_KEY) -> dict:
    """Return the licence data or raise ValueError with a user-facing reason."""
    key = "".join(key.split())
    if not key.upper().startswith("ERISMA-") or "." not in key:
        raise ValueError("This is not an Erisma licence key")
    body, sig = key[7:].split(".", 1)
    try:
        payload, signature = _unb32(body), _unb32(sig)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("The licence key is damaged — copy it again") from exc
    if not ed25519.verify(public, payload, signature):
        raise ValueError("The licence key is not valid")
    data = json.loads(payload)
    if data.get("expires") and date.fromisoformat(data["expires"]) < date.today():
        raise ValueError("The licence expired on {d}".format(d=data["expires"]))
    return data


def _state_file() -> Path:
    return home() / "license.json"


def _load() -> dict:
    try:
        return json.loads(_state_file().read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _save(st: dict) -> None:
    f = _state_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(st, indent=2), "utf-8")


def status(today: date | None = None) -> dict:
    today = today or date.today()
    st = _load()
    if st.get("key"):
        try:
            data = parse_key(st["key"])
            return {"state": "licensed", "name": data.get("name", ""), "plan": data.get("plan", ""),
                    "expires": data.get("expires", "")}
        except ValueError as exc:
            reason = str(exc)
        else:  # pragma: no cover
            reason = ""
    else:
        reason = ""
    if not st.get("trial_start"):
        st["trial_start"] = today.isoformat()
        try:
            _save(st)
        except OSError:
            pass
    start = date.fromisoformat(st["trial_start"])
    left = TRIAL_DAYS - (today - start).days
    if left > 0:
        return {"state": "trial", "days_left": left, "reason": reason}
    return {"state": "expired", "days_left": 0, "reason": reason,
            "since": (start + timedelta(days=TRIAL_DAYS)).isoformat()}


def activate(key: str) -> dict:
    data = parse_key(key)
    st = _load()
    st["key"] = "".join(key.split())
    _save(st)
    return data


def allowed() -> bool:
    if os.environ.get("ERISMA_NO_LICENSE_CHECK"):
        return True
    return status()["state"] != "expired"
