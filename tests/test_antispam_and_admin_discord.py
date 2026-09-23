import unittest
from milenium.modules import application_antispam, admin_discord


class TestApplicationAntispam(unittest.TestCase):
    def setUp(self):
        application_antispam.reset_rate_limits()

    def test_valid_submission(self):
        data = {
            "name": "Alex",
            "discord_tag": "alex#1234",
            "discord_id": "123456789012345678",
            "phone": "+1234567890",
            "email": "alex@example.com",
            "role_type": "main",
            "about": "Hello world"
        }
        ok, code, res = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="192.168.1.1",
            extra_signal="Mozilla/5.0"
        )
        self.assertTrue(ok)
        self.assertEqual(code, 200)
        self.assertEqual(res["status"], "success")
        self.assertIn("data", res)

    def test_honeypot_rejection_no_enumeration_leak(self):
        data = {
            "name": "Bot",
            "discord_id": "123456789012345678",
            "role_type": "main",
            "website": "http://spamsite.com"  # Honeypot filled by bot
        }
        ok, code, res = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="1.2.3.4",
            extra_signal="BotAgent"
        )
        self.assertFalse(ok)
        self.assertEqual(code, 400)
        self.assertEqual(res["message"], "Invalid submission.")
        # Ensure no leak of existing discord/phone
        self.assertNotIn("discord", res["message"].lower())
        self.assertNotIn("phone", res["message"].lower())

    def test_rate_limiting_ip_plus_signal(self):
        data = {
            "name": "Spammer",
            "discord_id": "123456789012345678",
            "role_type": "main"
        }
        # First 5 attempts should succeed
        for _ in range(5):
            ok, code, res = application_antispam.validate_and_process_application(
                form_data=data,
                client_ip="10.0.0.1",
                extra_signal="device-A"
            )
            self.assertTrue(ok)
            self.assertEqual(code, 200)

        # 6th attempt with same IP and signal should be rate limited (429)
        ok, code, res = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="10.0.0.1",
            extra_signal="device-A"
        )
        self.assertFalse(ok)
        self.assertEqual(code, 429)
        self.assertIn("Rate limit", res["message"])

        # Different signal/IP should not be blocked
        ok_other, code_other, _ = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="10.0.0.1",
            extra_signal="device-B"
        )
        self.assertTrue(ok_other)
        self.assertEqual(code_other, 200)

    def test_max_length_enforcement(self):
        data = {
            "name": "A" * 150,  # exceeds limit of 100
            "discord_id": "123456789012345678",
            "role_type": "main"
        }
        ok, code, res = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="127.0.0.1",
            extra_signal="test"
        )
        self.assertFalse(ok)
        self.assertEqual(code, 400)
        self.assertIn("exceeds maximum allowed length", res["message"])

    def test_invalid_role_type(self):
        data = {
            "name": "Sam",
            "discord_id": "123456789012345678",
            "role_type": "unknown_role"
        }
        ok, code, res = application_antispam.validate_and_process_application(
            form_data=data,
            client_ip="127.0.0.1",
            extra_signal="test"
        )
        self.assertFalse(ok)
        self.assertEqual(code, 400)
        self.assertIn("Invalid role_type", res["message"])


class TestAdminDiscordRole(unittest.TestCase):
    def setUp(self):
        admin_discord.reset_application_store()
        self.mock_settings = {
            "bot_token": "mock_bot_token",
            "guild_id": "111111111111111111",
            "main_role_id": "222222222222222222",
            "family_role_id": "333333333333333333",
        }

    def test_admin_session_required(self):
        ok, code, res = admin_discord.accept_application(
            application_id="app_123",
            discord_user_id="123456789012345678",
            target_role_type="main",
            session=None,
            custom_settings=self.mock_settings
        )
        self.assertFalse(ok)
        self.assertEqual(code, 401)
        self.assertIn("Admin session required", res["message"])

    def test_snowflake_validation(self):
        session = {"is_admin": True}
        # Invalid discord user ID (not numeric / wrong length)
        ok, code, res = admin_discord.accept_application(
            application_id="app_123",
            discord_user_id="not_a_snowflake",
            target_role_type="main",
            session=session,
            custom_settings=self.mock_settings
        )
        self.assertFalse(ok)
        self.assertEqual(code, 400)
        self.assertIn("Invalid Discord user ID", res["message"])

    def test_invalid_role_snowflake_setting(self):
        session = {"is_admin": True}
        bad_settings = dict(self.mock_settings)
        bad_settings["main_role_id"] = "bad_role"

        ok, code, res = admin_discord.accept_application(
            application_id="app_123",
            discord_user_id="123456789012345678",
            target_role_type="main",
            session=session,
            custom_settings=bad_settings
        )
        self.assertFalse(ok)
        self.assertEqual(code, 500)
        self.assertIn("Configuration error", res["message"])

    def test_successful_accept_and_mutual_exclusion(self):
        session = {"is_admin": True}
        calls = []

        def mock_assign(guild, user, add, remove, token):
            calls.append({"guild": guild, "user": user, "add": add, "remove": remove})
            return True, None

        # Accept as 'main'
        ok, code, res = admin_discord.accept_application(
            application_id="app_001",
            discord_user_id="123456789012345678",
            target_role_type="main",
            session=session,
            custom_settings=self.mock_settings,
            mock_discord_assign=mock_assign
        )
        self.assertTrue(ok)
        self.assertEqual(code, 200)
        self.assertEqual(res["role_assigned"], "main")
        self.assertFalse(res["is_repeat"])

        # Check mutual exclusion: added main_role_id (222...), removed family_role_id (333...)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["add"], "222222222222222222")
        self.assertEqual(calls[0]["remove"], "333333333333333333")

        # Now accept as 'family' for the same user: verifies mutual exclusion in reverse direction
        ok_fam, code_fam, res_fam = admin_discord.accept_application(
            application_id="app_002",
            discord_user_id="123456789012345678",
            target_role_type="family",
            session=session,
            custom_settings=self.mock_settings,
            mock_discord_assign=mock_assign
        )
        self.assertTrue(ok_fam)
        self.assertEqual(code_fam, 200)
        self.assertEqual(res_fam["role_assigned"], "family")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[1]["add"], "333333333333333333")
        self.assertEqual(calls[1]["remove"], "222222222222222222")

    def test_idempotent_accept(self):
        session = {"is_admin": True}
        call_count = 0

        def mock_assign(guild, user, add, remove, token):
            nonlocal call_count
            call_count += 1
            return True, None

        # First call
        ok1, code1, res1 = admin_discord.accept_application(
            application_id="app_repeat",
            discord_user_id="123456789012345678",
            target_role_type="family",
            session=session,
            custom_settings=self.mock_settings,
            mock_discord_assign=mock_assign
        )
        self.assertTrue(ok1)
        self.assertEqual(code1, 200)
        self.assertFalse(res1["is_repeat"])
        self.assertEqual(call_count, 1)

        # Repeated call should not call Discord API again
        ok2, code2, res2 = admin_discord.accept_application(
            application_id="app_repeat",
            discord_user_id="123456789012345678",
            target_role_type="family",
            session=session,
            custom_settings=self.mock_settings,
            mock_discord_assign=mock_assign
        )
        self.assertTrue(ok2)
        self.assertEqual(code2, 200)
        self.assertTrue(res2["is_repeat"])
        self.assertEqual(call_count, 1)  # Did not increment

    def test_discord_api_failure_visible_error(self):
        session = {"is_admin": True}

        def mock_failing_assign(guild, user, add, remove, token):
            return False, "Discord 403 Forbidden: Bot lacks hierarchy permissions. The bot's role must be positioned above Main and Family roles in the Discord server hierarchy."

        ok, code, res = admin_discord.accept_application(
            application_id="app_fail",
            discord_user_id="123456789012345678",
            target_role_type="main",
            session=session,
            custom_settings=self.mock_settings,
            mock_discord_assign=mock_failing_assign
        )
        self.assertFalse(ok)
        self.assertEqual(code, 502)
        self.assertIn("Bot lacks hierarchy permissions", res["message"])
        self.assertIn("hierarchy", res["message"].lower())


if __name__ == "__main__":
    unittest.main()
