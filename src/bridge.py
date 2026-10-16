#!/usr/bin/env python3

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional

import logger
from config import config
from definitions import ROOT_DIR, ADMIN_PATH, ALLOWLIST_PATH, CHATID_PATH
import radarr
import sonarr

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.bridge", logLevel, config.get("logToConsole", False))

_app = None
_listener = None


def is_user_authorized(telegram_uid: str, username: Optional[str] = None, check_admin: bool = False) -> bool:
    """Validate user authorization against allowlist, admin, or chatid files."""
    telegram_uid_str = str(telegram_uid).strip()
    username_str = str(username).strip() if username else ""

    # Check allowlist if enabled
    if config.get("enableAllowlist", False):
        if not os.path.exists(ALLOWLIST_PATH):
            return False
        with open(ALLOWLIST_PATH, "r", encoding="utf8") as f:
            allowed = False
            for line in f:
                cid = line.strip().split(" - ")[0]
                if cid and (cid == telegram_uid_str or (username_str and cid == username_str)):
                    allowed = True
                    break
            if not allowed:
                return False

    # Check admin if required or enabled
    if check_admin or config.get("enableAdmin", False):
        if not os.path.exists(ADMIN_PATH):
            return False
        with open(ADMIN_PATH, "r", encoding="utf8") as f:
            is_admin = False
            for line in f:
                cid = line.strip().split(" - ")[0]
                if cid and (cid == telegram_uid_str or (username_str and cid == username_str)):
                    is_admin = True
                    break
            if not is_admin:
                return False

    # Check authenticated chats in chatid.txt if file exists and has content
    if os.path.exists(CHATID_PATH):
        with open(CHATID_PATH, "r", encoding="utf8") as f:
            lines = [l.strip().split(" - ")[0] for l in f if l.strip()]
            if lines and telegram_uid_str not in lines:
                return False

    return True


def _resolve_tags(service_module, service_cfg: Dict[str, Any], user_id: Optional[str] = None, raw_tags=None) -> list:
    """Resolve tag labels or requester ID into integer tag IDs required by Radarr/Sonarr."""
    if isinstance(raw_tags, list) and raw_tags and all(isinstance(t, int) for t in raw_tags):
        return raw_tags

    tags = []
    try:
        existing_tags = service_module.getTags() or []
        if service_cfg.get("addRequesterIdTag") and user_id:
            if str(user_id) not in [str(t.get("label")) for t in existing_tags]:
                service_module.createTag(str(user_id))
                existing_tags = service_module.getTags() or []
            for t in existing_tags:
                if str(t.get("label")) == str(user_id):
                    tags.append(int(t["id"]))
        if not tags:
            label_list = raw_tags if raw_tags is not None else service_cfg.get("defaultTags", [])
            if label_list:
                tags = [int(t["id"]) for t in existing_tags if t.get("label") in label_list]
    except Exception as e:
        logger.warning(f"Could not resolve tags, defaulting to []: {e}")
    return tags


def dispatch_action(action: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Execute action against local Sonarr/Radarr APIs and return data."""
    try:
        if action == "search_movie":
            term = payload.get("term", "")
            raw = radarr.search(term)
            if raw:
                return {"success": True, "results": radarr.giveTitles(raw)}
            return {"success": True, "results": []}

        elif action == "search_series":
            term = payload.get("term", "")
            raw = sonarr.search(term)
            if raw:
                return {"success": True, "results": sonarr.giveTitles(raw)}
            return {"success": True, "results": []}

        elif action == "add_movie":
            tmdb_id = payload.get("tmdbId")
            path = payload.get("path")
            quality_profile_id = payload.get("qualityProfileId")
            tags = _resolve_tags(radarr, config.get("radarr", {}), user_id=user_id, raw_tags=payload.get("tags"))
            success = radarr.addToLibrary(tmdb_id, path, quality_profile_id, tags)
            return {"success": bool(success)}

        elif action == "add_series":
            tvdb_id = payload.get("tvdbId")
            path = payload.get("path")
            quality_profile_id = payload.get("qualityProfileId")
            tags = _resolve_tags(sonarr, config.get("sonarr", {}), user_id=user_id, raw_tags=payload.get("tags"))
            seasons_selected = payload.get("seasonsSelected")
            if seasons_selected is None:
                # default to all seasons monitored
                seasons_selected = sonarr.getSeasons(tvdb_id)
            success = sonarr.addToLibrary(tvdb_id, path, quality_profile_id, tags, seasons_selected)
            return {"success": bool(success)}

        elif action == "get_library_movies":
            items = radarr.get_library_summary()
            return {"success": items is not False, "items": items or []}

        elif action == "get_library_series":
            items = sonarr.get_library_summary()
            return {"success": items is not False, "items": items or []}

        elif action == "update_movie":
            movie_id = payload.get("movieId")
            profile_id = payload.get("qualityProfileId")
            monitored = payload.get("monitored")
            result = radarr.update_movie(movie_id, quality_profile_id=profile_id, monitored=monitored)
            return {"success": bool(result), "data": result}

        elif action == "update_series":
            series_id = payload.get("seriesId")
            profile_id = payload.get("qualityProfileId")
            monitored = payload.get("monitored")
            seasons = payload.get("seasons")
            result = sonarr.update_series(series_id, quality_profile_id=profile_id, monitored=monitored, seasons=seasons)
            return {"success": bool(result), "data": result}

        elif action == "delete_movie":
            tmdb_id = payload.get("tmdbId")
            result = radarr.removeFromLibrary(tmdb_id)
            return {"success": bool(result)}

        elif action == "delete_series":
            tvdb_id = payload.get("tvdbId")
            result = sonarr.removeFromLibrary(tvdb_id)
            return {"success": bool(result)}

        elif action == "get_config_options":
            return {
                "success": True,
                "radarr": {
                    "qualityProfiles": radarr.getQualityProfiles(),
                    "rootFolders": radarr.getRootFolders(),
                },
                "sonarr": {
                    "qualityProfiles": sonarr.getQualityProfiles(),
                    "rootFolders": sonarr.getRootFolders(),
                }
            }

        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    except Exception as e:
        logger.error(f"Error handling action '{action}': {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def process_request(db_module, user_id: str, req_id: str, request_data: Dict[str, Any]):
    """Process an individual request node from Firebase RTDB."""
    if not isinstance(request_data, dict):
        return

    action = request_data.get("action")
    payload = request_data.get("payload", {})
    username = request_data.get("username")

    logger.info(f"Processing bridge request req_id={req_id} action={action} user_id={user_id}")

    # Verify authorization
    if not is_user_authorized(user_id, username=username):
        logger.warning(f"Unauthorized bridge request from user_id={user_id}")
        response_payload = {"success": False, "error": "Unauthorized"}
    else:
        response_payload = dispatch_action(action, payload, user_id=user_id)

    # Post response to /responses/{user_id}/{req_id}
    try:
        resp_ref = db_module.reference(f"responses/{user_id}/{req_id}")
        resp_ref.set(response_payload)
        # Delete original request to keep queue clean
        req_ref = db_module.reference(f"requests/{user_id}/{req_id}")
        req_ref.delete()
    except Exception as e:
        logger.error(f"Failed to write bridge response for req_id={req_id}: {e}")


def init_firebase_app():
    """Initialize Firebase Admin app using configured credentials."""
    import firebase_admin
    from firebase_admin import credentials

    miniapp_cfg = config.get("miniapp", {})
    if not miniapp_cfg.get("enable", False):
        logger.info("Telegram Mini App bridge is disabled in config.")
        return None

    db_url = miniapp_cfg.get("databaseURL")
    if not db_url:
        logger.error("Mini App bridge is enabled but 'miniapp.databaseURL' is not configured.")
        return None

    sa_path = miniapp_cfg.get("serviceAccountPath", "serviceAccountKey.json")
    if not os.path.isabs(sa_path):
        sa_path = os.path.join(ROOT_DIR, sa_path)

    if not os.path.exists(sa_path):
        logger.warning(f"Service account file not found at: {sa_path}. Bridge will not start.")
        return None

    try:
        cred = credentials.Certificate(sa_path)
        app = firebase_admin.initialize_app(cred, {"databaseURL": db_url})
        logger.info("Firebase Admin initialized successfully for Mini App bridge.")
        return app
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin: {e}")
        return None


async def start_bridge_listener():
    """Asynchronous entry point that listens for requests on Firebase RTDB."""
    global _app
    miniapp_cfg = config.get("miniapp", {})
    if not miniapp_cfg.get("enable", False):
        return

    app = init_firebase_app()
    if not app:
        return

    _app = app
    from firebase_admin import db

    def on_request_event(event):
        """Callback triggered on Realtime Database change events."""
        try:
            # Event path could be '/' (initial load), '/{userId}', or '/{userId}/{reqId}'
            path = event.path.strip("/")
            data = event.data

            if not data:
                return

            parts = [p for p in path.split("/") if p]
            if len(parts) == 0:
                # Top-level: dict of user_id -> dict of req_id -> request_data
                if isinstance(data, dict):
                    for u_id, user_reqs in data.items():
                        if isinstance(user_reqs, dict):
                            for r_id, req in user_reqs.items():
                                process_request(db, u_id, r_id, req)
            elif len(parts) == 1:
                # /requests/{user_id}
                u_id = parts[0]
                if isinstance(data, dict):
                    for r_id, req in data.items():
                        process_request(db, u_id, r_id, req)
            elif len(parts) == 2:
                # /requests/{user_id}/{req_id}
                u_id, r_id = parts[0], parts[1]
                process_request(db, u_id, r_id, data)
        except Exception as err:
            logger.error(f"Error handling RTDB event: {err}", exc_info=True)

    requests_ref = db.reference("requests")
    # listen() runs in a background thread provided by Firebase Admin
    _listener = requests_ref.listen(on_request_event)
    logger.info("Mini App bridge is actively listening for incoming requests.")

    while True:
        await asyncio.sleep(60)
