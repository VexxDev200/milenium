import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional
from milenium.modules import config

# Regex pattern for Discord Snowflake ID (17 to 20 numeric digits)
SNOWFLAKE_REGEX = re.compile(r"^\d{17,20}$")

# Local in-memory store for application statuses to ensure idempotency across calls
# application_id -> { "status": "accepted", "role_assigned": "main"|"family", "discord_id": "...", ... }
_APPLICATION_STORE: Dict[str, Dict[str, Any]] = {}


def is_valid_snowflake(value: Any) -> bool:
    """Validates that a given string or integer matches the Discord Snowflake format."""
    if not value:
        return False
    val_str = str(value).strip()
    return bool(SNOWFLAKE_REGEX.match(val_str))


def get_discord_settings() -> Dict[str, str]:
    """
    Retrieves configured Discord settings from environment or config.
    - DISCORD_BOT_TOKEN
    - DISCORD_GUILD_ID
    - DISCORD_MAIN_ROLE_ID
    - DISCORD_FAMILY_ROLE_ID
    """
    return {
        "bot_token": config.get("DISCORD_BOT_TOKEN", "").strip(),
        "guild_id": config.get("DISCORD_GUILD_ID", "").strip(),
        "main_role_id": config.get("DISCORD_MAIN_ROLE_ID", "").strip(),
        "family_role_id": config.get("DISCORD_FAMILY_ROLE_ID", "").strip(),
    }


def validate_role_id(role_id: str, role_name: str = "Role") -> Tuple[bool, Optional[str]]:
    """Validates that the role ID is a valid snowflake."""
    if not role_id:
        return False, f"{role_name} ID is not configured."
    if not is_valid_snowflake(role_id):
        return False, f"Invalid {role_name} ID format '{role_id}'. Must be a valid Discord snowflake (17-20 digits)."
    return True, None


def is_admin_session(session: Optional[Dict[str, Any]]) -> bool:
    """
    Checks whether the caller has a valid admin session.
    Expects session to be non-empty and have is_admin=True or role='admin'.
    """
    if not session or not isinstance(session, dict):
        return False
    if session.get("is_admin") is True:
        return True
    if str(session.get("role", "")).lower() == "admin":
        return True
    return False


def _discord_api_request(
    method: str,
    endpoint: str,
    bot_token: str,
    payload: Optional[Dict[str, Any]] = None
) -> Tuple[int, Dict[str, Any], Optional[str]]:
    """
    Performs an HTTP request to the Discord API v10.
    Returns (status_code, response_data, error_message).
    """
    url = f"https://discord.com/api/v10{endpoint}"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "User-Agent": "MileniumDiscordBot/1.0",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            res_json = json.loads(body) if body else {}
            return status, res_json, None
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8")
        try:
            res_json = json.loads(body)
        except Exception:
            res_json = {"message": body}
        error_msg = res_json.get("message", f"HTTP {status}")
        return status, res_json, f"Discord API error ({status}): {error_msg}"
    except Exception as e:
        return 0, {}, f"Discord connection error: {str(e)}"


def get_member_roles(
    guild_id: str,
    user_id: str,
    bot_token: str
) -> Tuple[bool, list, Optional[str]]:
    """Fetches the current roles for a member in the guild."""
    status, data, err = _discord_api_request(
        "GET",
        f"/guilds/{guild_id}/members/{user_id}",
        bot_token
    )
    if err or status != 200:
        return False, [], err or f"Failed to get member, status {status}"
    return True, data.get("roles", []), None


def assign_discord_role(
    guild_id: str,
    user_id: str,
    role_to_add: str,
    role_to_remove: Optional[str],
    bot_token: str
) -> Tuple[bool, Optional[str]]:
    """
    Assigns role_to_add and removes role_to_remove (enforcing mutual exclusion) via Discord API.
    Handles hierarchy errors, invalid guild, or bad role with explicit visible error messages.
    """
    # 1. Remove the mutually exclusive role if specified
    if role_to_remove:
        status, _, err = _discord_api_request(
            "DELETE",
            f"/guilds/{guild_id}/members/{user_id}/roles/{role_to_remove}",
            bot_token
        )
        # 404 on role removal is okay if the member simply did not have the role
        if err and status not in (204, 404):
            if status == 403:
                return False, "Discord 403 Forbidden: Missing Permissions. Ensure the bot role is positioned higher than target roles in server hierarchy."
            if status == 404:
                return False, "Discord 404 Not Found: Guild, user, or role not found."
            return False, f"Failed to remove mutually exclusive role {role_to_remove}: {err}"

    # 2. Add the target role
    status, _, err = _discord_api_request(
        "PUT",
        f"/guilds/{guild_id}/members/{user_id}/roles/{role_to_add}",
        bot_token
    )
    if err and status != 204:
        if status == 403:
            return False, (
                "Discord 403 Forbidden: Bot lacks hierarchy permissions. "
                "The bot's role must be positioned above Main and Family roles in the Discord server hierarchy."
            )
        if status == 404:
            return False, "Discord 404 Not Found: Guild, user, or role does not exist."
        return False, f"Discord API error assigning role: {err}"

    return True, None


def accept_application(
    application_id: str,
    discord_user_id: str,
    target_role_type: str,
    session: Optional[Dict[str, Any]],
    custom_settings: Optional[Dict[str, str]] = None,
    mock_discord_assign: Optional[Any] = None
) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Accepts an application and assigns the corresponding Discord role:
    - Requires admin session -> 401 without it
    - Validates snowflake IDs for Discord user and roles
    - Idempotent: Repeated calls return existing accepted state without duplicate assignment
    - Mutual exclusion rule: 'main' and 'family' are mutually exclusive.
      Accepting as 'main' removes 'family' role; accepting as 'family' removes 'main' role.
    - Discord API failures (hierarchy, wrong guild, bad role) return visible error, never silent success.
    """
    # 1. Admin session requirement
    if not is_admin_session(session):
        return False, 401, {
            "status": "error",
            "message": "Unauthorized: Admin session required to accept applications."
        }

    # 2. Idempotency check: if application was already accepted with the same role, return immediately
    existing_app = _APPLICATION_STORE.get(application_id)
    target_role_type = target_role_type.lower()
    if existing_app and existing_app.get("status") == "accepted":
        if existing_app.get("assigned_role") == target_role_type:
            return True, 200, {
                "status": "success",
                "message": "Application already accepted (idempotent).",
                "application_id": application_id,
                "role_assigned": target_role_type,
                "discord_user_id": discord_user_id,
                "is_repeat": True
            }

    # 3. Target role type validation
    if target_role_type not in ("main", "family"):
        return False, 400, {
            "status": "error",
            "message": f"Invalid target_role_type '{target_role_type}'. Must be 'main' or 'family'."
        }

    # 4. Snowflake validation for Discord User ID
    if not is_valid_snowflake(discord_user_id):
        return False, 400, {
            "status": "error",
            "message": f"Invalid Discord user ID '{discord_user_id}'. Must be a valid Discord snowflake."
        }

    # 5. Discord settings & Role snowflake validation
    settings = custom_settings or get_discord_settings()
    bot_token = settings.get("bot_token", "")
    guild_id = settings.get("guild_id", "")
    main_role_id = settings.get("main_role_id", "")
    family_role_id = settings.get("family_role_id", "")

    ok_main, err_main = validate_role_id(main_role_id, "Main role")
    if not ok_main:
        return False, 500, {"status": "error", "message": f"Configuration error: {err_main}"}

    ok_fam, err_fam = validate_role_id(family_role_id, "Family role")
    if not ok_fam:
        return False, 500, {"status": "error", "message": f"Configuration error: {err_fam}"}

    if not is_valid_snowflake(guild_id):
        return False, 500, {
            "status": "error",
            "message": f"Configuration error: Discord Guild ID '{guild_id}' is not a valid snowflake."
        }

    # Determine which role to assign and which to remove (Mutual Exclusion Rule)
    if target_role_type == "main":
        role_to_add = main_role_id
        role_to_remove = family_role_id
    else:
        role_to_add = family_role_id
        role_to_remove = main_role_id

    # 6. Assign role via Discord API
    if mock_discord_assign:
        success, err = mock_discord_assign(guild_id, discord_user_id, role_to_add, role_to_remove, bot_token)
    else:
        if not bot_token:
            return False, 500, {
                "status": "error",
                "message": "Configuration error: DISCORD_BOT_TOKEN is not configured."
            }
        success, err = assign_discord_role(guild_id, discord_user_id, role_to_add, role_to_remove, bot_token)

    if not success:
        # Never silent success: visible error to admin
        return False, 502, {
            "status": "error",
            "message": f"Failed to assign Discord role: {err}"
        }

    # 7. Record state in application store for idempotency
    _APPLICATION_STORE[application_id] = {
        "status": "accepted",
        "assigned_role": target_role_type,
        "discord_user_id": discord_user_id,
        "role_id": role_to_add
    }

    return True, 200, {
        "status": "success",
        "message": f"Application accepted and Discord role '{target_role_type}' assigned.",
        "application_id": application_id,
        "role_assigned": target_role_type,
        "discord_user_id": discord_user_id,
        "is_repeat": False
    }


def reset_application_store():
    """Clear application store for tests."""
    _APPLICATION_STORE.clear()
