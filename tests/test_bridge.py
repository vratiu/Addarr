import hashlib
import hmac
import json
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import bridge


def _make_signed_init_data(user_id: int, bot_token: str, username: str = "testuser", auth_date: int = None) -> str:
    if auth_date is None:
        auth_date = int(time.time())
    user_json = json.dumps({"id": user_id, "first_name": "Test", "username": username}, separators=(",", ":"))
    items = sorted([
        f"auth_date={auth_date}",
        "query_id=AAHdF6IQAAAAAN0XohDhrOrc",
        f"user={user_json}",
    ])
    data_check_string = "\n".join(items)
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    sig = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"query_id=AAHdF6IQAAAAAN0XohDhrOrc&user={user_json}&auth_date={auth_date}&hash={sig}"


class TestBridge(unittest.TestCase):
    def setUp(self):
        bridge._rate_limit_buckets.clear()

    def test_is_user_authorized_fails_closed_when_unconfigured(self):
        with patch.dict(bridge.config, {"enableAllowlist": False, "enableAdmin": False}):
            with patch("os.path.exists", return_value=False):
                self.assertFalse(bridge.is_user_authorized("123456"))

    def test_is_user_authorized_chatid_file(self):
        with patch.dict(bridge.config, {"enableAllowlist": False, "enableAdmin": False}):
            with patch("os.path.exists", return_value=True):
                with patch("builtins.open", unittest.mock.mock_open(read_data="123456 - user1\n")):
                    self.assertTrue(bridge.is_user_authorized("123456"))
                    self.assertFalse(bridge.is_user_authorized("999999"))

    def test_is_user_authorized_allowlist(self):
        with patch.dict(bridge.config, {"enableAllowlist": True, "enableAdmin": False}):
            with patch("os.path.exists", side_effect=lambda p: p == bridge.ALLOWLIST_PATH):
                with patch("builtins.open", unittest.mock.mock_open(read_data="123456 - user1\n789012 - user2\n")):
                    self.assertTrue(bridge.is_user_authorized("123456"))
                    self.assertFalse(bridge.is_user_authorized("999999"))

    @patch("bridge.radarr.search")
    @patch("bridge.radarr.giveTitles")
    def test_dispatch_search_movie(self, mock_titles, mock_search):
        mock_search.return_value = [{"title": "Alien"}]
        mock_titles.return_value = [{"title": "Alien", "year": 1979}]

        res = bridge.dispatch_action("search_movie", {"term": "Alien"})
        self.assertTrue(res["success"])
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "Alien")

    @patch("bridge.radarr.update_movie")
    def test_dispatch_update_movie(self, mock_update):
        mock_update.return_value = {"id": 10, "qualityProfileId": 2, "monitored": True}

        res = bridge.dispatch_action("update_movie", {"movieId": 10, "qualityProfileId": 2, "monitored": True})
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["qualityProfileId"], 2)

    def test_process_request_flow_with_valid_signature(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        init_data = _make_signed_init_data(123456, bot_token)

        with patch.dict(bridge.config, {"telegram": {"token": bot_token}, "miniapp": {}}):
            with patch("bridge.is_user_authorized", return_value=True):
                with patch("bridge.dispatch_action", return_value={"success": True, "results": ["item1"]}):
                    bridge.process_request(
                        mock_db,
                        "123456",
                        "req_abc",
                        {"action": "search_movie", "payload": {"term": "Test"}, "initData": init_data}
                    )

        mock_db.reference.assert_any_call("responses/123456/req_abc")
        mock_ref.set.assert_called_with({"success": True, "results": ["item1"]})
        mock_db.reference.assert_any_call("requests/123456/req_abc")
        mock_ref.delete.assert_called()

    @patch("bridge.radarr.get_calendar_movies")
    def test_dispatch_get_calendar_movies(self, mock_cal):
        mock_cal.return_value = [{"title": "Avatar 3", "releaseDate": "2026-11-01"}]
        res = bridge.dispatch_action("get_calendar_movies", {"days": 30, "limit": 10})
        self.assertTrue(res["success"])
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["title"], "Avatar 3")
        mock_cal.assert_called_with(days=30, limit=10)

    @patch("bridge.sonarr.get_calendar_series")
    def test_dispatch_get_calendar_series(self, mock_cal):
        mock_cal.return_value = [{"title": "Severance", "episodeInfo": "S02E01"}]
        res = bridge.dispatch_action("get_calendar_series", {})
        self.assertTrue(res["success"])
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["items"][0]["title"], "Severance")
        mock_cal.assert_called_with(days=60, limit=20)

    def test_calendar_requires_admin_respects_config(self):
        with patch.dict(bridge.config, {"radarr": {"adminRestrictions": True}, "sonarr": {"adminRestrictions": False}}):
            self.assertTrue(bridge._requires_admin("get_calendar_movies"))
            self.assertFalse(bridge._requires_admin("get_calendar_series"))

        with patch.dict(bridge.config, {"radarr": {"adminRestrictions": False}, "sonarr": {"adminRestrictions": True}}):
            self.assertFalse(bridge._requires_admin("get_calendar_movies"))
            self.assertTrue(bridge._requires_admin("get_calendar_series"))

    def test_scrub_apikey(self):
        msg = "Error connecting to http://localhost:7878/api/v3?apikey=supersecret123&other=val"
        scrubbed = bridge._scrub_apikey(msg)
        self.assertNotIn("supersecret123", scrubbed)
        self.assertIn("apikey=***", scrubbed)
        self.assertIn("&other=val", scrubbed)

    def test_resolve_tags_exception_handling(self):
        mock_service = MagicMock()
        mock_service.getTags.side_effect = Exception("Connection error: apikey=mysecretkey")
        tags = bridge._resolve_tags(mock_service, {"defaultTags": ["test"]})
        self.assertEqual(tags, [])


    @patch("bridge.radarr.get_discover_movies")
    def test_dispatch_get_discover_movies(self, mock_discover):
        mock_discover.return_value = [{"id": 101, "title": "Dune 3", "year": 2026, "poster": "poster.jpg"}]
        res = bridge.dispatch_action("get_discover_movies", {"limit": 10})
        self.assertTrue(res["success"])
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "Dune 3")
        mock_discover.assert_called_with(limit=10)

    def test_discover_movies_requires_admin_respects_config(self):
        with patch.dict(bridge.config, {"radarr": {"adminRestrictions": True}}):
            self.assertTrue(bridge._requires_admin("get_discover_movies"))
        with patch.dict(bridge.config, {"radarr": {"adminRestrictions": False}}):
            self.assertFalse(bridge._requires_admin("get_discover_movies"))

    @patch("radarr.requests.get")
    def test_radarr_get_discover_movies_filtering_and_caching(self, mock_get):
        import radarr
        radarr._discover_cache = {"timestamp": 0.0, "items": []}

        # Mock API returning items including existing and excluded
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = json.dumps([
            {"tmdbId": 1, "title": "Movie 1", "year": 2024, "imdbId": "tt001", "isExisting": False, "isExcluded": False, "images": [{"coverType": "poster", "remoteUrl": "url1"}]},
            {"tmdbId": 2, "title": "Movie 2", "year": 2024, "isExisting": True, "isExcluded": False},  # Should be filtered
            {"tmdbId": 3, "title": "Movie 3", "year": 2024, "isExisting": False, "isExcluded": True},  # Should be filtered
            {"tmdbId": 1, "title": "Movie 1 Dup", "year": 2024, "isExisting": False, "isExcluded": False},  # Duplicate
            {"tmdbId": 4, "title": "Movie 4", "year": 2025, "isExisting": False, "isExcluded": False, "images": [{"coverType": "banner", "url": "b1"}], "remotePoster": "remote4"},
        ])
        mock_get.return_value = mock_resp

        results = radarr.get_discover_movies(limit=24)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], 1)
        self.assertEqual(results[0]["poster"], "url1")
        self.assertEqual(results[0]["imdbId"], "tt001")
        self.assertEqual(results[1]["id"], 4)
        self.assertEqual(results[1]["poster"], "remote4")
        self.assertIsNone(results[1].get("imdbId"))
        self.assertEqual(mock_get.call_count, 1)

        # Verify URL called with includeRecommendations=false
        called_url = mock_get.call_args[0][0]
        self.assertIn("includeRecommendations=false", called_url)
        self.assertIn("includeTrending=true", called_url)
        self.assertIn("includePopular=true", called_url)

        # 2nd call should hit cache and NOT call requests.get again
        cached_results = radarr.get_discover_movies(limit=1)
        self.assertEqual(len(cached_results), 1)
        self.assertEqual(cached_results[0]["id"], 1)
        self.assertEqual(mock_get.call_count, 1)

    @patch("radarr.requests.post")
    @patch("radarr.requests.get")
    def test_radarr_add_to_library_evicts_discover_cache(self, mock_get, mock_post):
        import radarr
        radarr._discover_cache = {
            "timestamp": time.time(),
            "items": [
                {"id": 100, "title": "Movie 100"},
                {"id": 200, "title": "Movie 200"},
            ]
        }

        # Mock lookup
        mock_lookup = MagicMock()
        mock_lookup.status_code = 200
        mock_lookup.text = json.dumps({"tmdbId": 100, "year": 2025, "title": "Movie 100", "titleSlug": "m100", "images": []})
        mock_get.return_value = mock_lookup

        # Mock add success (201)
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 201
        mock_post.return_value = mock_post_resp

        added = radarr.addToLibrary(100, "/movies", 1, [])
        self.assertTrue(added)

        # Check that 100 was evicted from cache
        remaining_ids = [m["id"] for m in radarr._discover_cache["items"]]
        self.assertNotIn(100, remaining_ids)
        self.assertIn(200, remaining_ids)


if __name__ == "__main__":
    unittest.main()

