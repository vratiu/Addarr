import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Ensure fake config exists if config.yaml is not present
import config as app_config
if not hasattr(app_config, "config") or not app_config.config:
    app_config.config = {
        "radarr": {
            "server": {"addr": "127.0.0.1", "port": 7878, "path": "/", "ssl": False},
            "auth": {"apikey": "fake_radarr_key"},
            "minimumAvailability": "announced",
            "search": True
        },
        "sonarr": {
            "server": {"addr": "127.0.0.1", "port": 8989, "path": "/", "ssl": False},
            "auth": {"apikey": "fake_sonarr_key"},
            "seasonFolder": True,
            "search": True
        }
    }

import radarr
import sonarr


class TestLibraryMutations(unittest.TestCase):
    @patch("radarr.requests.get")
    def test_radarr_get_library_summary(self, mock_get):
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps([
            {
                "id": 101,
                "tmdbId": 550,
                "title": "Fight Club",
                "year": 1999,
                "images": [{"coverType": "poster", "remoteUrl": "https://image.tmdb.org/poster.jpg"}],
                "qualityProfileId": 1,
                "monitored": True,
                "status": "released",
                "hasFile": True,
                "sizeOnDisk": 4500000000
            }
        ])
        mock_get.return_value = fake_response

        summary = radarr.get_library_summary()
        self.assertIsNotNone(summary)
        self.assertEqual(len(summary), 1)
        item = summary[0]
        self.assertEqual(item["id"], 101)
        self.assertEqual(item["title"], "Fight Club")
        self.assertEqual(item["poster"], "https://image.tmdb.org/poster.jpg")
        self.assertEqual(item["qualityProfileId"], 1)
        self.assertTrue(item["monitored"])

    @patch("radarr.requests.put")
    @patch("radarr.requests.get")
    def test_radarr_update_movie(self, mock_get, mock_put):
        get_res = MagicMock()
        get_res.status_code = 200
        get_res.text = json.dumps({
            "id": 101,
            "title": "Fight Club",
            "qualityProfileId": 1,
            "monitored": False
        })
        mock_get.return_value = get_res

        put_res = MagicMock()
        put_res.status_code = 200
        put_res.text = json.dumps({
            "id": 101,
            "title": "Fight Club",
            "qualityProfileId": 3,
            "monitored": True
        })
        mock_put.return_value = put_res

        updated = radarr.update_movie(101, quality_profile_id=3, monitored=True)
        self.assertIsNotNone(updated)
        self.assertEqual(updated["qualityProfileId"], 3)
        self.assertTrue(updated["monitored"])
        self.assertTrue(mock_put.called)
        put_payload = mock_put.call_args[1]["json"]
        self.assertEqual(put_payload["qualityProfileId"], 3)
        self.assertTrue(put_payload["monitored"])

    @patch("sonarr.requests.get")
    def test_sonarr_get_library_summary(self, mock_get):
        fake_response = MagicMock()
        fake_response.status_code = 200
        fake_response.text = json.dumps([
            {
                "id": 202,
                "tvdbId": 121361,
                "title": "Game of Thrones",
                "year": 2011,
                "images": [{"coverType": "poster", "remoteUrl": "https://artworks.thetvdb.com/poster.jpg"}],
                "qualityProfileId": 2,
                "monitored": True,
                "status": "ended",
                "statistics": {"seasonCount": 8, "episodeCount": 73, "episodeFileCount": 73},
                "seasons": [{"seasonNumber": 1, "monitored": True}]
            }
        ])
        mock_get.return_value = fake_response

        summary = sonarr.get_library_summary()
        self.assertIsNotNone(summary)
        self.assertEqual(len(summary), 1)
        item = summary[0]
        self.assertEqual(item["id"], 202)
        self.assertEqual(item["title"], "Game of Thrones")
        self.assertEqual(item["poster"], "https://artworks.thetvdb.com/poster.jpg")
        self.assertEqual(item["seasonCount"], 8)
        self.assertTrue(item["monitored"])

    @patch("sonarr.requests.put")
    @patch("sonarr.requests.get")
    def test_sonarr_update_series(self, mock_get, mock_put):
        get_res = MagicMock()
        get_res.status_code = 200
        get_res.text = json.dumps({
            "id": 202,
            "title": "Game of Thrones",
            "qualityProfileId": 1,
            "monitored": False,
            "seasons": [
                {"seasonNumber": 1, "monitored": False},
                {"seasonNumber": 2, "monitored": False}
            ]
        })
        mock_get.return_value = get_res

        put_res = MagicMock()
        put_res.status_code = 200
        put_res.text = json.dumps({
            "id": 202,
            "title": "Game of Thrones",
            "qualityProfileId": 2,
            "monitored": True,
            "seasons": [
                {"seasonNumber": 1, "monitored": True},
                {"seasonNumber": 2, "monitored": False}
            ]
        })
        mock_put.return_value = put_res

        updated = sonarr.update_series(
            202,
            quality_profile_id=2,
            monitored=True,
            seasons=[{"seasonNumber": 1, "monitored": True}]
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["qualityProfileId"], 2)
        self.assertTrue(updated["monitored"])
        self.assertTrue(mock_put.called)
        put_payload = mock_put.call_args[1]["json"]
        self.assertEqual(put_payload["qualityProfileId"], 2)
        self.assertTrue(put_payload["monitored"])
        self.assertTrue(put_payload["seasons"][0]["monitored"])
        self.assertFalse(put_payload["seasons"][1]["monitored"])


if __name__ == "__main__":
    unittest.main()
