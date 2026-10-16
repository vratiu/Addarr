import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import bridge
import radarr
import sonarr


class TestEndToEndMiniAppFlow(unittest.TestCase):
    def test_full_miniapp_lifecycle_flow(self):
        # 1. Verification of User Authorization
        user_id = "123456789"
        with patch.dict(bridge.config, {"enableAllowlist": False, "enableAdmin": False}):
            with patch("os.path.exists", return_value=False):
                self.assertTrue(bridge.is_user_authorized(user_id))

        # 2. Search Media Action
        with patch("bridge.radarr.search", return_value=[{"title": "Dune", "tmdbId": 438631, "year": 2021, "overview": "Sci-fi epic"}]), \
             patch("bridge.radarr.giveTitles", return_value=[{"title": "Dune", "id": 438631, "year": 2021, "poster": "http://img.jpg"}]):
            search_res = bridge.dispatch_action("search_movie", {"term": "Dune"})
            self.assertTrue(search_res["success"])
            self.assertEqual(len(search_res["results"]), 1)
            self.assertEqual(search_res["results"][0]["title"], "Dune")

        # 3. Quick-Add Action
        with patch("bridge.radarr.addToLibrary", return_value=True) as mock_add:
            add_res = bridge.dispatch_action("add_movie", {
                "tmdbId": 438631,
                "path": "/movies",
                "qualityProfileId": 1
            })
            self.assertTrue(add_res["success"])
            default_tags = bridge.config.get("radarr", {}).get("defaultTags", [])
            mock_add.assert_called_with(438631, "/movies", 1, default_tags)

        # 4. View Library Summary Action
        with patch("bridge.radarr.get_library_summary", return_value=[{
            "id": 10,
            "tmdbId": 438631,
            "title": "Dune",
            "year": 2021,
            "poster": "http://img.jpg",
            "qualityProfileId": 1,
            "monitored": True,
            "status": "released"
        }]):
            lib_res = bridge.dispatch_action("get_library_movies", {})
            self.assertTrue(lib_res["success"])
            self.assertEqual(len(lib_res["items"]), 1)
            self.assertEqual(lib_res["items"][0]["title"], "Dune")

        # 5. Update Preferences (Season Monitoring in Sonarr)
        with patch("bridge.sonarr.update_series", return_value={
            "id": 20,
            "qualityProfileId": 3,
            "monitored": True,
            "seasons": [{"seasonNumber": 1, "monitored": False}, {"seasonNumber": 2, "monitored": True}]
        }) as mock_update_series:
            update_res = bridge.dispatch_action("update_series", {
                "seriesId": 20,
                "qualityProfileId": 3,
                "monitored": True,
                "seasons": [{"seasonNumber": 1, "monitored": False}, {"seasonNumber": 2, "monitored": True}]
            })
            self.assertTrue(update_res["success"])
            self.assertEqual(update_res["data"]["qualityProfileId"], 3)
            self.assertTrue(update_res["data"]["seasons"][1]["monitored"])

        # 6. Delete Action
        with patch("bridge.radarr.removeFromLibrary", return_value=True) as mock_del:
            del_res = bridge.dispatch_action("delete_movie", {"tmdbId": 438631})
            self.assertTrue(del_res["success"])
            mock_del.assert_called_with(438631)


if __name__ == "__main__":
    unittest.main()
