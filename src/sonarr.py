#!/usr/bin/env python3

import json
import logging

import requests

import commons as commons
import logger
from config import config

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.sonarr", logLevel, config.get("logToConsole", False))

config = config["sonarr"]

addSerieNeededFields = ["tvdbId", "tvRageId", "title", "titleSlug", "images", "seasons"]
REQUEST_TIMEOUT = 15


def search(title):
    parameters = {"term": title}
    req = requests.get(
        commons.generateApiQuery("sonarr", "series/lookup", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    parsed_json = json.loads(req.text)

    if req.status_code == 200 and parsed_json:
        return parsed_json
    else:
        return False


def giveTitles(parsed_json):
    data = []
    for show in parsed_json:
        if all(
            x in show
            for x in ["title", "statistics", "year", "tvdbId"]
        ):
            data.append(
                {
                    "title": show["title"],
                    "seasonCount": show["statistics"]["seasonCount"],
                    "poster": show.get("remotePoster", None),
                    "year": show["year"],
                    "id": show["tvdbId"],
                    "monitored": show["monitored"],
                    "status": show["status"],
                }
            )
    return data


def inLibrary(tvdbId):
    parameters = {}
    req = requests.get(commons.generateApiQuery("sonarr", "series", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return next((True for show in parsed_json if show["tvdbId"] == tvdbId), False)


def addToLibrary(tvdbId, path, qualityProfileId, tags, seasonsSelected):
    parameters = {"term": "tvdb:" + str(int(tvdbId))}
    req = requests.get(
        commons.generateApiQuery("sonarr", "series/lookup", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    parsed_json = json.loads(req.text)
    data = json.dumps(buildData(parsed_json, path, qualityProfileId, tags, seasonsSelected))
    add = requests.post(
        commons.generateApiQuery("sonarr", "series"),
        data=data,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if add.status_code == 201:
        return True
    else:
        return False


def removeFromLibrary(tvdbId):
    parameters = {
        "deleteFiles": str(True)
    }
    dbId = getDbIdFromImdbId(tvdbId)
    if dbId is None:
        return False
    delete = requests.delete(
        commons.generateApiQuery("sonarr", f"series/{int(dbId)}", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    if delete.status_code == 200:
        return True
    else:
        return False


def buildData(json, path, qualityProfileId, tags, seasonsSelected):
    built_data = {
        "qualityProfileId": int(qualityProfileId),
        "addOptions": {
            "ignoreEpisodesWithFiles": True,
            "ignoreEpisodesWithoutFiles": False,
            "searchForMissingEpisodes": config["search"],
        },
        "rootFolderPath": path,
        "seasonFolder": config["seasonFolder"],
        "monitored": True,
        "tags": tags,
        "seasons": seasonsSelected,
    }
    for show in json:
        for key, value in show.items():
            if key in addSerieNeededFields:
                built_data[key] = value
            if key == "seasons":
                built_data["seasons"] = seasonsSelected
    return built_data


def getRootFolders():
    parameters = {}
    req = requests.get(commons.generateApiQuery("sonarr", "Rootfolder", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    # Remove unmappedFolders from rootFolder data--we don't need that
    for item in [
        item for item in parsed_json if item.get("unmappedFolders") is not None
    ]:
        item.pop("unmappedFolders")
    return parsed_json


def allSeries():
    parameters = {}
    req = requests.get(commons.generateApiQuery("sonarr", "series", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)

    if req.status_code == 200:
        data = []
        for show in parsed_json:
            if all(
                x in show
                for x in ["title", "year", "monitored", "status"]
            ):
                data.append(
                    {
                        "title": show["title"],
                        "year": show["year"],
                        "monitored": show["monitored"],
                        "status": show["status"],
                    }
                )
        return data
    else:
        return False


def getQualityProfiles():
    parameters = {}
    req = requests.get(commons.generateApiQuery("sonarr", "qualityProfile", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return parsed_json


def getTags():
    parameters = {}
    req = requests.get(commons.generateApiQuery("sonarr", "tag", parameters), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    return parsed_json


def createTag(tag):
    data_json = {
        "id": int(max([t["id"] for t in getTags()], default=0) + 1),
        "label": str(tag)
    }
    add = requests.post(
        commons.generateApiQuery("sonarr", "tag"),
        json=data_json,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if add.status_code in (200, 201):
        return True
    else:
        return False


def getSeasons(tvdbId):
    parameters = {"term": "tvdb:" + str(int(tvdbId))}
    req = requests.get(
        commons.generateApiQuery("sonarr", "series/lookup", parameters),
        timeout=REQUEST_TIMEOUT,
    )
    parsed_json = json.loads(req.text)
    if not parsed_json:
        return []
    return parsed_json[0].get("seasons", [])


def getDbIdFromImdbId(tvdbId):
    req = requests.get(commons.generateApiQuery("sonarr", "series", {}), timeout=REQUEST_TIMEOUT)
    parsed_json = json.loads(req.text)
    dbId = [f["id"] for f in parsed_json if f["tvdbId"] == int(tvdbId)]
    return dbId[0] if dbId else None


def get_library_summary():
    req = requests.get(commons.generateApiQuery("sonarr", "series", {}), timeout=REQUEST_TIMEOUT)
    if req.status_code == 200:
        parsed_json = json.loads(req.text)
        data = []
        for show in parsed_json:
            poster = None
            for img in show.get("images", []):
                if img.get("coverType") == "poster":
                    poster = img.get("remoteUrl") or img.get("url")
                    break
            data.append(
                {
                    "id": show.get("id"),
                    "tvdbId": show.get("tvdbId"),
                    "title": show.get("title"),
                    "year": show.get("year"),
                    "poster": poster or show.get("remotePoster"),
                    "qualityProfileId": show.get("qualityProfileId"),
                    "monitored": show.get("monitored"),
                    "status": show.get("status"),
                    "seasonCount": show.get("statistics", {}).get("seasonCount", len(show.get("seasons", []))),
                    "episodeCount": show.get("statistics", {}).get("episodeCount", 0),
                    "episodeFileCount": show.get("statistics", {}).get("episodeFileCount", 0),
                    "seasons": show.get("seasons", []),
                }
            )
        return data
    return False


def update_series(series_id, quality_profile_id=None, monitored=None, seasons=None):
    safe_series_id = int(series_id)
    url = commons.generateApiQuery("sonarr", f"series/{safe_series_id}", {})
    req = requests.get(url, timeout=REQUEST_TIMEOUT)
    if req.status_code != 200:
        return False
    series = json.loads(req.text)
    if quality_profile_id is not None:
        series["qualityProfileId"] = int(quality_profile_id)
    if monitored is not None:
        series["monitored"] = bool(monitored)
    if seasons is not None:
        season_map = {int(s["seasonNumber"]): bool(s["monitored"]) for s in seasons if "seasonNumber" in s and "monitored" in s}
        for s in series.get("seasons", []):
            if s.get("seasonNumber") in season_map:
                s["monitored"] = season_map[s["seasonNumber"]]

    put_url = commons.generateApiQuery("sonarr", f"series/{safe_series_id}", {})
    res = requests.put(
        put_url,
        json=series,
        headers={'Content-Type': 'application/json'},
        timeout=REQUEST_TIMEOUT,
    )
    if res.status_code in (200, 202):
        return json.loads(res.text) if res.text else True
    return False



