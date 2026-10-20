import json
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

# Ensure src directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Ensure fake config exists if config.yaml is not present
import config as app_config
app_config.config.setdefault("radarr", {})
app_config.config["radarr"].setdefault("server", {})
if not app_config.config["radarr"]["server"].get("addr"):
    app_config.config["radarr"]["server"]["addr"] = "127.0.0.1"
    app_config.config["radarr"]["server"]["port"] = 7878
    app_config.config["radarr"]["server"]["path"] = "/"
    app_config.config["radarr"]["server"]["ssl"] = False
app_config.config["radarr"].setdefault("auth", {})
if not app_config.config["radarr"]["auth"].get("apikey"):
    app_config.config["radarr"]["auth"]["apikey"] = "fake_radarr_key"
app_config.config["radarr"].setdefault("minimumAvailability", "announced")
app_config.config["radarr"].setdefault("search", True)

app_config.config.setdefault("sonarr", {})
app_config.config["sonarr"].setdefault("server", {})
if not app_config.config["sonarr"]["server"].get("addr"):
    app_config.config["sonarr"]["server"]["addr"] = "127.0.0.1"
    app_config.config["sonarr"]["server"]["port"] = 8989
    app_config.config["sonarr"]["server"]["path"] = "/"
    app_config.config["sonarr"]["server"]["ssl"] = False
app_config.config["sonarr"].setdefault("auth", {})
if not app_config.config["sonarr"]["auth"].get("apikey"):
    app_config.config["sonarr"]["auth"]["apikey"] = "fake_sonarr_key"
app_config.config["sonarr"].setdefault("seasonFolder", True)
app_config.config["sonarr"].setdefault("search", True)

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

    @patch("radarr.requests.get")
    def test_radarr_get_calendar_movies(self, mock_get):
        today = datetime.now(timezone.utc).date()
        in_3_days = (today + timedelta(days=3)).isoformat()
        in_10_days = (today + timedelta(days=10)).isoformat()
        in_70_days = (today + timedelta(days=70)).isoformat()

        fake_movies = [
            {
                "id": 1,
                "tmdbId": 101,
                "title": "Movie In 10 Days",
                "year": 2026,
                "digitalRelease": in_10_days,
                "inCinemas": (today - timedelta(days=30)).isoformat(),
                "images": [{"coverType": "poster", "remoteUrl": "https://img/10.jpg"}],
                "monitored": True,
                "hasFile": False,
            },
            {
                "id": 2,
                "tmdbId": 102,
                "title": "Movie In 3 Days",
                "year": 2026,
                "digitalRelease": in_3_days,
                "inCinemas": (today - timedelta(days=20)).isoformat(),
                "images": [{"coverType": "poster", "remoteUrl": "https://img/3.jpg"}],
                "monitored": True,
                "hasFile": True,
            },
            {
                "id": 3,
                "tmdbId": 103,
                "title": "Cinema Only Movie",
                "year": 2026,
                "digitalRelease": None,
                "inCinemas": in_3_days,
                "images": [],
                "monitored": True,
                "hasFile": False,
            },
            {
                "id": 4,
                "tmdbId": 104,
                "title": "Too Far Movie",
                "year": 2026,
                "digitalRelease": in_70_days,
                "images": [],
                "monitored": True,
                "hasFile": False,
            },
        ]
        fake_res = MagicMock()
        fake_res.status_code = 200
        fake_res.text = json.dumps(fake_movies)
        mock_get.return_value = fake_res

        results = radarr.get_calendar_movies(days=60, limit=20)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)
        # Verify sorted ascending by digital release
        self.assertEqual(results[0]["title"], "Movie In 3 Days")
        self.assertEqual(results[0]["releaseDate"], in_3_days)
        self.assertEqual(results[0]["format"], "digital")
        self.assertTrue(results[0]["hasFile"])
        self.assertEqual(results[1]["title"], "Movie In 10 Days")
        self.assertEqual(results[1]["releaseDate"], in_10_days)

    @patch("radarr.requests.get")
    def test_radarr_give_titles_enrichment(self, mock_get):
        # 1. Existing movie with id > 0 where lookup has hasFile=False, but detailed GET /movie/{id} returns hasFile=True
        existing_lookup = [
            {
                "id": 42,
                "tmdbId": 550,
                "title": "Fight Club",
                "year": 1999,
                "overview": "An insomniac office worker...",
                "images": [{"coverType": "poster", "remoteUrl": "https://img/poster.jpg"}],
                "hasFile": False,
                "monitored": True,
                "imdbId": "tt0137523"
            }
        ]
        detailed_movie = {
            "id": 42,
            "tmdbId": 550,
            "title": "Fight Club",
            "qualityProfileId": 3,
            "monitored": True,
            "status": "released",
            "hasFile": True,
            "sizeOnDisk": 4500000000
        }
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = json.dumps(detailed_movie)
        mock_get.return_value = mock_res

        titles = radarr.giveTitles(existing_lookup)
        self.assertEqual(len(titles), 1)
        item = titles[0]
        self.assertEqual(item["id"], 550)  # id remains tmdbId
        self.assertTrue(item["inLibrary"])
        self.assertEqual(item["libraryId"], 42)
        self.assertEqual(item["qualityProfileId"], 3)
        self.assertTrue(item["monitored"])
        self.assertTrue(item["hasFile"])
        self.assertEqual(item["poster"], "https://img/poster.jpg")
        self.assertEqual(item["imdbId"], "tt0137523")

        # 2. Non-existing movie with id == 0 or missing
        new_lookup = [
            {
                "id": 0,
                "tmdbId": 999,
                "title": "New Movie",
                "year": 2026,
                "overview": "Brand new movie",
                "remotePoster": "https://img/new.jpg"
            }
        ]
        new_titles = radarr.giveTitles(new_lookup)
        self.assertEqual(len(new_titles), 1)
        new_item = new_titles[0]
        self.assertEqual(new_item["id"], 999)
        self.assertFalse(new_item["inLibrary"])
        self.assertNotIn("libraryId", new_item)

    @patch("sonarr.requests.get")
    def test_sonarr_give_titles_enrichment(self, mock_get):
        # 1. Existing series with id > 0 where lookup lacks episodeFileCount, but detailed GET /series/{id} returns episodeFileCount > 0
        existing_lookup = [
            {
                "id": 88,
                "tvdbId": 121361,
                "title": "Game of Thrones",
                "year": 2011,
                "overview": "Seven noble families fight for control...",
                "images": [{"coverType": "poster", "remoteUrl": "https://img/got.jpg"}],
                "statistics": {
                    "seasonCount": 8,
                    "episodeCount": 73,
                    "episodeFileCount": 0
                }
            }
        ]
        detailed_series = {
            "id": 88,
            "tvdbId": 121361,
            "title": "Game of Thrones",
            "qualityProfileId": 2,
            "monitored": True,
            "status": "ended",
            "statistics": {
                "seasonCount": 8,
                "episodeCount": 73,
                "episodeFileCount": 73
            },
            "seasons": [
                {"seasonNumber": 1, "monitored": True}
            ]
        }
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.text = json.dumps(detailed_series)
        mock_get.return_value = mock_res

        titles = sonarr.giveTitles(existing_lookup)
        self.assertEqual(len(titles), 1)
        item = titles[0]
        self.assertEqual(item["id"], 121361)  # id remains tvdbId
        self.assertTrue(item["inLibrary"])
        self.assertEqual(item["libraryId"], 88)
        self.assertEqual(item["qualityProfileId"], 2)
        self.assertTrue(item["monitored"])
        self.assertEqual(item["seasonCount"], 8)
        self.assertEqual(item["episodeFileCount"], 73)
        self.assertEqual(item["poster"], "https://img/got.jpg")
        self.assertEqual(len(item["seasons"]), 1)

        # 2. Non-existing series with id == 0 or missing
        new_lookup = [
            {
                "id": 0,
                "tvdbId": 54321,
                "title": "New Series",
                "year": 2026,
                "overview": "Upcoming show",
                "remotePoster": "https://img/show.jpg",
                "monitored": False,
                "status": "continuing",
                "statistics": {
                    "seasonCount": 1,
                    "episodeCount": 10,
                    "episodeFileCount": 0
                }
            }
        ]
        new_titles = sonarr.giveTitles(new_lookup)
        self.assertEqual(len(new_titles), 1)
        new_item = new_titles[0]
        self.assertEqual(new_item["id"], 54321)
        self.assertFalse(new_item["inLibrary"])
        self.assertNotIn("libraryId", new_item)

    @patch("sonarr.requests.get")
    def test_sonarr_get_calendar_series(self, mock_get):
        today = datetime.now(timezone.utc).date()
        in_2_days = (today + timedelta(days=2)).isoformat()
        in_5_days = (today + timedelta(days=5)).isoformat()
        in_80_days = (today + timedelta(days=80)).isoformat()

        fake_episodes = [
            # Two episodes of Severance on the same day -> should be grouped
            {
                "id": 501,
                "seriesId": 10,
                "seasonNumber": 2,
                "episodeNumber": 1,
                "title": "Hello",
                "airDate": in_2_days,
                "airDateUtc": f"{in_2_days}T00:00:00Z",
                "hasFile": False,
                "monitored": True,
                "series": {
                    "id": 10,
                    "tvdbId": 999,
                    "title": "Severance",
                    "year": 2022,
                    "images": [{"coverType": "poster", "remoteUrl": "https://img/sev.jpg"}],
                },
            },
            {
                "id": 502,
                "seriesId": 10,
                "seasonNumber": 2,
                "episodeNumber": 2,
                "title": "Goodbye",
                "airDate": in_2_days,
                "airDateUtc": f"{in_2_days}T01:00:00Z",
                "hasFile": False,
                "monitored": True,
                "series": {
                    "id": 10,
                    "tvdbId": 999,
                    "title": "Severance",
                    "year": 2022,
                    "images": [{"coverType": "poster", "remoteUrl": "https://img/sev.jpg"}],
                },
            },
            # Single episode of another show on in_5_days
            {
                "id": 601,
                "seriesId": 20,
                "seasonNumber": 1,
                "episodeNumber": 4,
                "title": "Solo Ep",
                "airDate": in_5_days,
                "airDateUtc": f"{in_5_days}T00:00:00Z",
                "hasFile": True,
                "monitored": True,
                "series": {
                    "id": 20,
                    "tvdbId": 888,
                    "title": "Slow Horses",
                    "year": 2022,
                    "images": [],
                },
            },
            # Far future episode -> should be excluded
            {
                "id": 701,
                "seriesId": 30,
                "seasonNumber": 1,
                "episodeNumber": 1,
                "title": "Far Away",
                "airDate": in_80_days,
                "airDateUtc": f"{in_80_days}T00:00:00Z",
                "hasFile": False,
                "monitored": True,
                "series": {"id": 30, "title": "Future Show"},
            },
        ]
        fake_res = MagicMock()
        fake_res.status_code = 200
        fake_res.text = json.dumps(fake_episodes)
        mock_get.return_value = fake_res

        results = sonarr.get_calendar_series(days=60, limit=20)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)

        # First entry: Severance grouped
        first = results[0]
        self.assertEqual(first["title"], "Severance")
        self.assertEqual(first["seasonNumber"], 2)
        self.assertEqual(first["episodeNumber"], 1)
        self.assertEqual(first["endEpisodeNumber"], 2)
        self.assertEqual(first["episodeCount"], 2)
        self.assertIn("S02E01-E02", first["episodeInfo"])
        self.assertEqual(first["releaseDate"], in_2_days)
        self.assertEqual(first["poster"], "https://img/sev.jpg")

        # Second entry: Slow Horses single episode
        second = results[1]
        self.assertEqual(second["title"], "Slow Horses")
        self.assertEqual(second["seasonNumber"], 1)
        self.assertEqual(second["episodeNumber"], 4)
        self.assertIsNone(second["endEpisodeNumber"])
        self.assertEqual(second["episodeCount"], 1)
        self.assertEqual(second["episodeInfo"], "S01E04")
        self.assertEqual(second["episodeTitle"], "Solo Ep")
        self.assertEqual(second["releaseDate"], in_5_days)
        self.assertTrue(second["hasFile"])


if __name__ == "__main__":
    unittest.main()

