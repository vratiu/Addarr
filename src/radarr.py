#!/usr/bin/env python3

import json
import logging
import time
from datetime import datetime, timedelta, timezone

import requests

import commons as commons
import logger
from config import config

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.radarr", logLevel, config.get("logToConsole", False))

config = config["radarr"]

addMovieNeededFields = ["tmdbId", "year", "title", "titleSlug", "images"]
REQUEST_TIMEOUT = 15

DISCOVER_CACHE_TTL = 3600  # 1 hour
_discover_cache = {"timestamp": 0.0, "items": []}


def search(title):
    parameters = {"term": title}
    url = commons.generateApiQuery("radarr", "movie/lookup", parameters)
    req = requests.get(url, timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)

    if req.status_code == 200 and parsed_json:
        return parsed_json
    else:
        return False


def giveTitles(parsed_json):
    data = []
    for movie in parsed_json:
        if all(
            x in movie for x in ["title", "overview", "year", "tmdbId"]
        ):
            poster = None
            for img in movie.get("images", []):
                if isinstance(img, dict) and img.get("coverType") == "poster":
                    poster = img.get("remoteUrl") or img.get("url")
                    break

            raw_id = movie.get("id")
            in_library = bool(raw_id and int(raw_id) > 0)

            # If movie is in library, fetch actual library record to guarantee hasFile, monitored, etc. are accurate
            lib_movie = None
            if in_library:
                try:
                    lib_url = commons.generateApiQuery("radarr", f"movie/{int(raw_id)}", {})
                    lib_res = requests.get(lib_url, timeout=REQUEST_TIMEOUT)
                    if lib_res.status_code == 200:
                        lib_movie = json.loads(lib_res.text)
                except Exception as e:
                    logger.debug(f"Could not fetch detailed movie for id {raw_id}: {e}")

            item = {
                "title": movie["title"],
                "overview": movie["overview"],
                "poster": poster or movie.get("remotePoster", None),
                "year": movie["year"],
                "id": movie["tmdbId"],
                "imdbId": movie.get("imdbId"),
                "inLibrary": in_library,
            }

            if in_library:
                src = lib_movie if lib_movie else movie
                item["libraryId"] = int(raw_id)
                if src.get("qualityProfileId") is not None:
                    item["qualityProfileId"] = int(src["qualityProfileId"])
                if "monitored" in src:
                    item["monitored"] = bool(src["monitored"])
                if "status" in src:
                    item["status"] = src["status"]
                if "hasFile" in src:
                    item["hasFile"] = bool(src["hasFile"])
                if "sizeOnDisk" in src:
                    item["sizeOnDisk"] = src["sizeOnDisk"]

            data.append(item)
    return data


def inLibrary(tmdbId):
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "movie", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return next((True for movie in parsed_json if movie["tmdbId"] == tmdbId), False)


def addToLibrary(tmdbId, path, qualityProfileId, tags):
    parameters = {"tmdbId": str(int(tmdbId))}
    req = requests.get(
        commons.generateApiQuery("radarr", "movie/lookup/tmdb", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    parsed_json = json.loads(req.text)
    data = json.dumps(buildData(parsed_json, path, qualityProfileId, tags))
    add = requests.post(
        commons.generateApiQuery("radarr", "movie"),
        data=data,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if add.status_code == 201:
        # Evict from discover suggestions cache if present
        try:
            target_id = int(tmdbId)
            _discover_cache["items"] = [
                m for m in _discover_cache.get("items", []) if m.get("id") != target_id
            ]
        except Exception as e:
            logger.warning(f"Could not evict tmdbId={tmdbId} from discover cache: {e}")
        return True
    else:
        return False


def removeFromLibrary(tmdbId):
    parameters = {
        "deleteFiles": str(True)
    }
    dbId = getDbIdFromImdbId(tmdbId)
    if dbId is None:
        return False
    delete = requests.delete(
        commons.generateApiQuery("radarr", f"movie/{int(dbId)}", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    if delete.status_code == 200:
        return True
    else:
        return False


def buildData(json, path, qualityProfileId, tags):
    built_data = {
        "qualityProfileId": int(qualityProfileId),
        "minimumAvailability": config["minimumAvailability"],
        "rootFolderPath": path,
        "addOptions": {"searchForMovie": config["search"]},
        "tags": tags,
    }

    for key in addMovieNeededFields:
        built_data[key] = json[key]
    return built_data


def getRootFolders():
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "Rootfolder", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return parsed_json


def all_movies():
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "movie", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)

    if req.status_code == 200:
        data = []
        for movie in parsed_json:
            if all(
                x in movie
                for x in ["title", "year", "monitored", "status"]
            ):
                data.append(
                    {
                        "title": movie["title"],
                        "year": movie["year"],
                        "monitored": movie["monitored"],
                        "status": movie["status"]
                    }
                )
        return data
    else:
        return False


def getQualityProfiles():
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "qualityProfile", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return parsed_json


def getTags():
    parameters = {}
    req = requests.get(commons.generateApiQuery("radarr", "tag", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return parsed_json


def createTag(tag):
    data_json = {
        "id": max([t["id"] for t in getTags()], default=0) + 1,
        "label": str(tag)
    }
    add = requests.post(
        commons.generateApiQuery("radarr", "tag"),
        json=data_json,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if add.status_code in (200, 201):
        return True
    else:
        return False


def getDbIdFromImdbId(tmdbId):
    req = requests.get(commons.generateApiQuery("radarr", "movie", {}), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    dbId = [f["id"] for f in parsed_json if f["tmdbId"] == int(tmdbId)]
    return dbId[0] if dbId else None


def get_library_summary():
    req = requests.get(commons.generateApiQuery("radarr", "movie", {}), timeout=REQUEST_TIMEOUT)
    if req.status_code == 200:
        parsed_json = json.loads(req.text)
        data = []
        for movie in parsed_json:
            poster = None
            for img in movie.get("images", []):
                if img.get("coverType") == "poster":
                    poster = img.get("remoteUrl") or img.get("url")
                    break
            data.append(
                {
                    "id": movie.get("id"),
                    "tmdbId": movie.get("tmdbId"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "poster": poster or movie.get("remotePoster"),
                    "qualityProfileId": movie.get("qualityProfileId"),
                    "monitored": movie.get("monitored"),
                    "status": movie.get("status"),
                    "hasFile": movie.get("hasFile", False),
                    "sizeOnDisk": movie.get("sizeOnDisk", 0),
                }
            )
        return data
    return False


def update_movie(movie_id, quality_profile_id=None, monitored=None):
    safe_movie_id = int(movie_id)
    url = commons.generateApiQuery("radarr", f"movie/{safe_movie_id}", {})
    req = requests.get(url, timeout=REQUEST_TIMEOUT)
    if req.status_code != 200:
        return False
    movie = json.loads(req.text)
    if quality_profile_id is not None:
        movie["qualityProfileId"] = int(quality_profile_id)
    if monitored is not None:
        movie["monitored"] = bool(monitored)

    put_url = commons.generateApiQuery("radarr", f"movie/{safe_movie_id}", {})
    res = requests.put(
        put_url,
        json=movie,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if res.status_code in (200, 202):
        return json.loads(res.text) if res.text else True
    return False


def get_calendar_movies(days=60, limit=20):
    now = datetime.now(timezone.utc)
    start_date = now.date()
    end_date = start_date + timedelta(days=int(days))

    parameters = {
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "unmonitored": "false",
    }
    url = commons.generateApiQuery("radarr", "calendar", parameters)
    req = requests.get(url, timeout=REQUEST_TIMEOUT)
    if req.status_code == 200:
        movies = json.loads(req.text)
        data = []
        for movie in movies:
            digital_release = movie.get("digitalRelease")
            if not digital_release:
                continue
            try:
                rel_date_str = str(digital_release)[:10]
                rel_date = datetime.strptime(rel_date_str, "%Y-%m-%d").date()
            except Exception:
                continue
            if not (start_date <= rel_date <= end_date):
                continue

            poster = None
            for img in movie.get("images", []):
                if img.get("coverType") == "poster":
                    poster = img.get("remoteUrl") or img.get("url")
                    break

            data.append(
                {
                    "id": movie.get("id"),
                    "tmdbId": movie.get("tmdbId"),
                    "title": movie.get("title"),
                    "year": movie.get("year"),
                    "poster": poster or movie.get("remotePoster"),
                    "releaseDate": rel_date_str,
                    "releaseDateIso": digital_release,
                    "format": "digital",
                    "monitored": movie.get("monitored", True),
                    "hasFile": movie.get("hasFile", False),
                }
            )
        data.sort(key=lambda m: (m["releaseDate"], m["title"]))
        return data[:int(limit)]
    return False


def get_discover_movies(limit=24):
    """
    Fetch movie suggestions from Radarr's Discover feed (importlist/movie)
    with includeRecommendations=true, includeTrending=true, includePopular=true.
    Caches results in memory for DISCOVER_CACHE_TTL (1 hour) to avoid hammering Radarr.
    Filters out existing and excluded movies, and deduplicates by tmdbId.
    """
    now = time.time()
    cached_items = _discover_cache.get("items", [])
    cache_ts = _discover_cache.get("timestamp", 0.0)

    # Return from cache if fresh and populated
    if cached_items and (now - cache_ts < DISCOVER_CACHE_TTL):
        return cached_items[:int(limit)]

    parameters = {
        "includeRecommendations": "false",
        "includeTrending": "true",
        "includePopular": "true",
    }
    url = commons.generateApiQuery("radarr", "importlist/movie", parameters)
    try:
        req = requests.get(url, timeout=REQUEST_TIMEOUT)
    except Exception as e:
        logger.error(f"Failed to query Radarr discover endpoint: {e}")
        # If upstream fails but we have stale cache, return stale cache gracefully
        if cached_items:
            return cached_items[:int(limit)]
        return False

    if req.status_code == 200:
        try:
            movies = json.loads(req.text)
        except Exception as e:
            logger.error(f"Failed to parse Radarr discover response JSON: {e}")
            if cached_items:
                return cached_items[:int(limit)]
            return False

        if not isinstance(movies, list):
            if cached_items:
                return cached_items[:int(limit)]
            return False

        seen_tmdb_ids = set()
        data = []
        for movie in movies:
            if not isinstance(movie, dict):
                continue

            # Exclude already existing or excluded titles
            if movie.get("isExisting") or movie.get("isExcluded"):
                continue

            tmdb_id = movie.get("tmdbId")
            if not tmdb_id:
                continue

            try:
                tmdb_id = int(tmdb_id)
            except (ValueError, TypeError):
                continue

            if tmdb_id in seen_tmdb_ids:
                continue
            seen_tmdb_ids.add(tmdb_id)

            poster = None
            for img in movie.get("images", []):
                if isinstance(img, dict) and img.get("coverType") == "poster":
                    poster = img.get("remoteUrl") or img.get("url")
                    break

            data.append(
                {
                    "id": tmdb_id,
                    "title": movie.get("title", ""),
                    "year": movie.get("year", 0),
                    "overview": movie.get("overview", "") or "",
                    "poster": poster or movie.get("remotePoster"),
                    "imdbId": movie.get("imdbId"),
                }
            )

        _discover_cache["timestamp"] = now
        _discover_cache["items"] = data
        return data[:int(limit)]

    # If status code not 200, return stale cache if present or False
    if cached_items:
        return cached_items[:int(limit)]
    return False