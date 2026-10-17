import asyncio
import hashlib
import hmac
import json
import os
import sys
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import bridge
import commons
import radarr
import sonarr
import transmission
import sabnzbd


def _make_signed_init_data(user_id: int, bot_token: str, username: str = "alice", auth_date: int = None) -> str:
    if auth_date is None:
        auth_date = int(time.time())
    user_json = json.dumps({"id": user_id, "first_name": "Alice", "username": username}, separators=(",", ":"))
    items = sorted([
        f"auth_date={auth_date}",
        "query_id=AAHdF6IQAAAAAN0XohDhrOrc",
        f"user={user_json}",
    ])
    data_check_string = "\n".join(items)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    sig = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"query_id=AAHdF6IQAAAAAN0XohDhrOrc&user={user_json}&auth_date={auth_date}&hash={sig}"


class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        bridge._rate_limit_buckets.clear()
        commons._auth_failures.clear()
        self.bot_token = "999888777:AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKK12"

    # 1. Bridge initData Signature & UID Spoofing Tests
    def test_bridge_rejects_missing_init_data(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref

        with patch.dict(bridge.config, {"telegram": {"token": self.bot_token}, "miniapp": {}}):
            with patch("bridge.dispatch_action") as mock_dispatch:
                bridge.process_request(
                    mock_db,
                    "123456",
                    "req_1",
                    {"action": "get_library_movies", "payload": {}}
                )
                self.assertFalse(mock_dispatch.called)
                mock_ref.set.assert_called_with({"success": False, "error": "Unauthorized: invalid Telegram session"})
                mock_ref.delete.assert_called()

    def test_bridge_rejects_uid_spoofing_mismatch(self):
        """Signed initData for user 111111 cannot execute requests under path /requests/999999."""
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        init_data_for_111 = _make_signed_init_data(111111, self.bot_token)

        with patch.dict(bridge.config, {"telegram": {"token": self.bot_token}, "miniapp": {}}):
            with patch("bridge.dispatch_action") as mock_dispatch:
                bridge.process_request(
                    mock_db,
                    "999999",
                    "req_spoof",
                    {"action": "delete_movie", "payload": {"tmdbId": 550}, "initData": init_data_for_111}
                )
                self.assertFalse(mock_dispatch.called)
                mock_ref.set.assert_called_with({"success": False, "error": "Unauthorized: invalid Telegram session"})

    def test_bridge_rejects_future_dated_init_data(self):
        future_ts = int(time.time()) + 3600
        init_data = _make_signed_init_data(123456, self.bot_token, auth_date=future_ts)
        is_valid, user = bridge.verify_telegram_init_data(init_data, self.bot_token)
        self.assertFalse(is_valid)
        self.assertIsNone(user)

    def test_bridge_rejects_unsafe_rtdb_keys(self):
        mock_db = MagicMock()
        bridge.process_request(mock_db, "../responses/123", "req_1", {"action": "search_movie"})
        self.assertFalse(mock_db.reference.called)

    # 2. Rate Limiting & Stale Request Tests
    def test_bridge_enforces_per_user_rate_limit(self):
        user_id = "444555"
        for _ in range(bridge.RATE_LIMIT_MAX_REQUESTS):
            self.assertTrue(bridge._check_rate_limit(user_id))
        self.assertFalse(bridge._check_rate_limit(user_id))

    def test_bridge_discards_stale_requests(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        stale_ts = int((time.time() - 600) * 1000)  # 10 minutes old

        with patch("bridge.dispatch_action") as mock_dispatch:
            bridge.process_request(
                mock_db,
                "123456",
                "req_stale",
                {"action": "search_movie", "timestamp": stale_ts}
            )
            self.assertFalse(mock_dispatch.called)
            mock_ref.delete.assert_called_once()

    # 3. Admin Restrictions & Folder/Profile Filtering
    def test_bridge_enforces_admin_on_delete_when_enable_admin_true(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        init_data = _make_signed_init_data(123456, self.bot_token, username="regular_user")

        def fake_exists(path):
            return path in (bridge.CHATID_PATH, bridge.ADMIN_PATH)

        def fake_open(path, *args, **kwargs):
            if path == bridge.CHATID_PATH:
                return unittest.mock.mock_open(read_data="123456 - regular_user\n")()
            if path == bridge.ADMIN_PATH:
                return unittest.mock.mock_open(read_data="999999 - admin_user\n")()
            raise FileNotFoundError(path)

        with patch.dict(bridge.config, {
            "telegram": {"token": self.bot_token},
            "enableAdmin": True,
            "enableAllowlist": False,
            "miniapp": {},
        }):
            with patch("os.path.exists", side_effect=fake_exists), \
                 patch("builtins.open", side_effect=fake_open), \
                 patch("bridge.dispatch_action") as mock_dispatch:
                # Delete must be blocked for non-admin
                bridge.process_request(
                    mock_db,
                    "123456",
                    "req_del",
                    {"action": "delete_movie", "payload": {"tmdbId": 550}, "initData": init_data}
                )
                self.assertFalse(mock_dispatch.called)
                mock_ref.set.assert_called_with({"success": False, "error": "Unauthorized"})

    def test_bridge_blocks_excluded_and_traversal_root_folders(self):
        with patch.dict(bridge.config, {
            "radarr": {"excludedRootFolders": ["/mnt/restricted"]}
        }):
            res1 = bridge.dispatch_action("add_movie", {
                "tmdbId": 550,
                "path": "/mnt/restricted",
                "qualityProfileId": 1,
            })
            self.assertFalse(res1["success"])
            self.assertIn("restricted", res1["error"])

            res2 = bridge.dispatch_action("add_movie", {
                "tmdbId": 550,
                "path": "/movies/../../etc",
                "qualityProfileId": 1,
            })
            self.assertFalse(res2["success"])

    def test_bridge_filters_config_options(self):
        with patch.dict(bridge.config, {
            "radarr": {
                "excludedRootFolders": ["/secret_movies"],
                "excludedQualityProfiles": ["4K-Remux"],
            },
            "sonarr": {
                "excludedRootFolders": [],
                "excludedQualityProfiles": [],
            },
        }), patch("bridge.radarr.getRootFolders", return_value=[
            {"id": 1, "path": "/movies"},
            {"id": 2, "path": "/secret_movies"},
        ]), patch("bridge.radarr.getQualityProfiles", return_value=[
            {"id": 1, "name": "HD-1080p"},
            {"id": 2, "name": "4K-Remux"},
        ]), patch("bridge.sonarr.getRootFolders", return_value=[]), \
            patch("bridge.sonarr.getQualityProfiles", return_value=[]):
            res = bridge.dispatch_action("get_config_options", {})
            self.assertTrue(res["success"])
            self.assertEqual(len(res["radarr"]["rootFolders"]), 1)
            self.assertEqual(res["radarr"]["rootFolders"][0]["path"], "/movies")
            self.assertEqual(len(res["radarr"]["qualityProfiles"]), 1)
            self.assertEqual(res["radarr"]["qualityProfiles"][0]["name"], "HD-1080p")

    # 4. SSRF / Path Traversal / Query Parameter Injection & API Key Scrubbing
    def test_generate_api_query_encodes_params_and_blocks_traversal(self):
        with patch.dict(commons.config, {
            "radarr": {
                "server": {"addr": "127.0.0.1", "port": 7878, "path": "/", "ssl": False},
                "auth": {"apikey": "supersecretkey"},
            }
        }):
            # Attempt parameter injection via search term
            url = commons.generateApiQuery("radarr", "movie/lookup", {"term": "dune&deleteFiles=true#foo"})
            self.assertIn("term=dune%26deleteFiles%3Dtrue%23foo", url)

            # Attempt path traversal in endpoint
            bad_url = commons.generateApiQuery("radarr", "movie/../../system/backup", {})
            self.assertIsNone(bad_url)

    def test_bridge_scrubs_api_key_from_exception_responses(self):
        with patch("bridge.radarr.search", side_effect=RuntimeError(
            "HTTPConnectionPool(host='192.168.1.50', port=7878): Max retries exceeded with url: /api/v3/movie/lookup?apikey=SECRET_KEY_12345&term=test"
        )):
            res = bridge.dispatch_action("search_movie", {"term": "test"})
            self.assertFalse(res["success"])
            self.assertNotIn("SECRET_KEY_12345", res["error"])
            self.assertNotIn("192.168.1.50", res["error"])

    def test_update_movie_rejects_non_integer_id_traversal(self):
        res = bridge.dispatch_action("update_movie", {"movieId": "1/../command", "monitored": True})
        self.assertFalse(res["success"])
        self.assertIn("Invalid request parameters", res["error"])

    # 5. Transmission & SABnzbd Security Tests
    def test_transmission_uses_subprocess_list_and_blocks_non_admin(self):
        update = MagicMock()
        update.effective_message.chat_id = 111
        update.callback_query.data = str(transmission.TSL_LIMIT)
        context = MagicMock()
        context.bot.send_message = AsyncMock()

        with patch.dict(transmission.config, {
            "enable": True,
            "onlyAdmin": True,
            "host": "127.0.0.1; touch /tmp/pwned",
            "authentication": True,
            "username": "admin",
            "password": "$(whoami)",
        }):
            # Non-admin must be rejected before subprocess.run
            with patch("transmission.checkId", return_value=True), \
                 patch("transmission.checkAllowed", return_value=False), \
                 patch("transmission.subprocess.run") as mock_run:
                asyncio.run(transmission.changeSpeedTransmission(update, context))
                self.assertFalse(mock_run.called)

            # Admin executes subprocess.run with argument list (no shell)
            with patch("transmission.checkId", return_value=True), \
                 patch("transmission.checkAllowed", return_value=True), \
                 patch("transmission.subprocess.run") as mock_run:
                asyncio.run(transmission.changeSpeedTransmission(update, context))
                self.assertTrue(mock_run.called)
                called_cmd = mock_run.call_args[0][0]
                self.assertIsInstance(called_cmd, list)
                self.assertEqual(called_cmd[0], "transmission-remote")
                self.assertIn("--alt-speed", called_cmd)

    def test_sabnzbd_rejects_injected_callback_choice(self):
        update = MagicMock()
        update.effective_message.chat_id = 111
        update.callback_query.data = "100&mode=shutdown"
        context = MagicMock()
        context.bot.send_message = AsyncMock()

        with patch.dict(sabnzbd.config, {"enable": True, "onlyAdmin": False}):
            with patch("sabnzbd.checkId", return_value=True), \
                 patch("sabnzbd.requests.get") as mock_get:
                asyncio.run(sabnzbd.changeSpeedSabnzbd(update, context))
                self.assertFalse(mock_get.called)

    # 6. Commons Auth Brute-Force Lockout & Long Message Formatting
    def test_auth_rate_limiting_blocks_brute_force(self):
        chat_id = 555666
        for _ in range(commons.AUTH_MAX_FAILURES):
            self.assertFalse(commons._is_auth_rate_limited(chat_id))
            commons._record_auth_failure(chat_id)
        self.assertTrue(commons._is_auth_rate_limited(chat_id))

    def test_format_long_list_message_splits_over_4096_chars(self):
        many_items = [
            {"title": f"Movie Title Number {i}", "year": 2024, "status": "released", "monitored": True}
            for i in range(150)
        ]
        parts = commons.format_long_list_message(many_items)
        self.assertIsInstance(parts, list)
        self.assertTrue(len(parts) > 1)
        for part in parts:
            self.assertIsInstance(part, str)
            self.assertLessEqual(len(part), 4096)


if __name__ == "__main__":
    unittest.main()
