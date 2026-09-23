import time
import re
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Tuple, Optional
from milenium.modules import config

# Max length restrictions server-side for all application fields
FIELD_LIMITS: Dict[str, int] = {
    "name": 100,
    "discord_tag": 64,      # e.g. username or username#1234
    "discord_id": 32,       # snowflake string
    "phone": 32,
    "email": 128,
    "age": 8,
    "about": 1000,
    "role_type": 16,        # 'main' or 'family'
    "website": 256,         # honeypot field name (hidden from humans)
}

# In-memory rate limiting store: key -> list of timestamps
_RATE_LIMIT_STORE: Dict[str, list] = {}

# Rate limit configuration: 5 applications per 10 minutes (600s) per key
RATE_LIMIT_WINDOW = 600
RATE_LIMIT_MAX_ATTEMPTS = 5


def get_rate_limit_key(ip: str, extra_signal: Optional[str] = None) -> str:
    """
    Combines IP + another signal (e.g. user-agent, session id, or device hash)
    to form the rate limit identifier.
    """
    clean_ip = (ip or "127.0.0.1").strip()
    clean_extra = (extra_signal or "default").strip()
    return f"{clean_ip}:{clean_extra}"


def check_rate_limit(key: str, now: Optional[float] = None) -> bool:
    """
    Returns True if request is allowed, False if rate limited.
    """
    if now is None:
        now = time.time()
    
    timestamps = _RATE_LIMIT_STORE.get(key, [])
    # Filter out expired timestamps
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    
    if len(valid_timestamps) >= RATE_LIMIT_MAX_ATTEMPTS:
        _RATE_LIMIT_STORE[key] = valid_timestamps
        return False
        
    valid_timestamps.append(now)
    _RATE_LIMIT_STORE[key] = valid_timestamps
    return True


def reset_rate_limits():
    """Clear in-memory rate limits (primarily for testing)."""
    _RATE_LIMIT_STORE.clear()


def verify_captcha_if_configured(captcha_response: Optional[str], remote_ip: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Checks for captcha secret only if already present in environment patterns.
    (e.g., RECAPTCHA_SECRET_KEY, HCAPTCHA_SECRET_KEY, TURNSTILE_SECRET_KEY, CAPTCHA_SECRET).
    If no secret is present in environment/config, captcha verification is skipped (returns True).
    If a secret is present, captcha verification is enforced.
    """
    captcha_secret = (
        config.get("CAPTCHA_SECRET")
        or config.get("RECAPTCHA_SECRET_KEY")
        or config.get("HCAPTCHA_SECRET_KEY")
        or config.get("TURNSTILE_SECRET_KEY")
    )
    if not captcha_secret:
        return True, None

    if not captcha_response:
        return False, "Captcha token is required"

    # Cloudflare Turnstile / hCaptcha / reCAPTCHA standard siteverify API
    siteverify_url = config.get(
        "CAPTCHA_VERIFY_URL",
        "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        if "TURNSTILE" in (config.get("CAPTCHA_TYPE", "").upper())
        else "https://www.google.com/recaptcha/api/siteverify"
    )

    try:
        data = urllib.parse.urlencode({
            "secret": captcha_secret,
            "response": captcha_response,
            "remoteip": remote_ip or ""
        }).encode("utf-8")
        req = urllib.request.Request(siteverify_url, data=data, headers={"User-Agent": "Milenium-Captcha-Verifier/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            if res_json.get("success"):
                return True, None
            return False, "Captcha validation failed"
    except Exception as e:
        return False, f"Captcha verification service error: {e}"


def validate_and_process_application(
    form_data: Dict[str, Any],
    client_ip: str,
    extra_signal: Optional[str] = None,
    captcha_token: Optional[str] = None
) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Validates form data with anti-spam protections:
    1. Server-side rate limit (IP + extra signal)
    2. Honeypot hidden field detection (no enumeration leak)
    3. Server-side max length validation on all fields
    4. Safe submission handling without leaking whether Discord or phone exists
    """
    # 1. Rate Limiting
    rl_key = get_rate_limit_key(client_ip, extra_signal)
    if not check_rate_limit(rl_key):
        return False, 429, {"status": "error", "message": "Rate limit exceeded. Please try again later."}

    # 2. Honeypot check
    # Bots fill hidden fields (such as 'website' or 'hp_email').
    # Reject without leaking enumeration or specific honeypot details.
    honeypot_val = form_data.get("website") or form_data.get("hp_field")
    if honeypot_val:
        # Return generic submission rejected status to prevent bot heuristics
        return False, 400, {"status": "error", "message": "Invalid submission."}

    # 3. Check for captcha if configured in env
    captcha_ok, captcha_err = verify_captcha_if_configured(captcha_token or form_data.get("captcha_token"), client_ip)
    if not captcha_ok:
        return False, 400, {"status": "error", "message": captcha_err or "Captcha validation failed."}

    # 4. Max length limits check on all submitted fields
    cleaned_data: Dict[str, Any] = {}
    for field_name, value in form_data.items():
        if value is None:
            continue
        val_str = str(value)
        limit = FIELD_LIMITS.get(field_name, 255)
        if len(val_str) > limit:
            return False, 400, {
                "status": "error",
                "message": f"Field '{field_name}' exceeds maximum allowed length of {limit} characters."
            }
        cleaned_data[field_name] = val_str.strip()

    # Required field validation
    required_fields = ["discord_id", "role_type"]
    for req in required_fields:
        if not cleaned_data.get(req):
            return False, 400, {"status": "error", "message": f"Missing required field: '{req}'."}

    # Role type validation: only 'main' or 'family'
    role_type = cleaned_data.get("role_type", "").lower()
    if role_type not in ("main", "family"):
        return False, 400, {"status": "error", "message": "Invalid role_type. Must be 'main' or 'family'."}

    cleaned_data["role_type"] = role_type

    # Generic success response that DOES NOT enumerate existing applications
    # Even if duplicate applications exist in database, return standard success message.
    return True, 200, {
        "status": "success",
        "message": "Application received and is pending review.",
        "data": cleaned_data
    }
