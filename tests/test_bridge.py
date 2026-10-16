import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import bridge


class TestBridge(unittest.TestCase):
    def test_is_user_authorized_no_restrictions(self):
        with patch.dict(bridge.config, {"enableAllowlist": False, "enableAdmin": False}):
            with patch("os.path.exists", return_value=False):
                self.assertTrue(bridge.is_user_authorized("123456"))

    def test_is_user_authorized_allowlist(self):
        with patch.dict(bridge.config, {"enableAllowlist": True, "enableAdmin": False}):
            with patch("os.path.exists", return_value=True):
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

    def test_process_request_flow(self):
        mock_db = MagicMock()
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref

        with patch("bridge.is_user_authorized", return_value=True):
            with patch("bridge.dispatch_action", return_value={"success": True, "results": ["item1"]}):
                bridge.process_request(
                    mock_db,
                    "user123",
                    "req_abc",
                    {"action": "search_movie", "payload": {"term": "Test"}}
                )

        mock_db.reference.assert_any_call("responses/user123/req_abc")
        mock_ref.set.assert_called_with({"success": True, "results": ["item1"]})
        mock_db.reference.assert_any_call("requests/user123/req_abc")
        mock_ref.delete.assert_called()


if __name__ == "__main__":
    unittest.main()
