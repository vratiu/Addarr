import hmac
import logging
import math
import os
import time
from urllib.parse import quote
from telegram.ext import ConversationHandler
import logger
from config import config
from definitions import ADMIN_PATH, CHATID_PATH, ALLOWLIST_PATH
from translations import i18n

# Set up logging
logLevel = logging.DEBUG if config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.commons", logLevel, config.get("logToConsole", False))

# Per-chat brute-force rate limiter for /auth: chat_id -> list of failure timestamps
_auth_failures = {}
AUTH_MAX_FAILURES = 5
AUTH_LOCKOUT_SECONDS = 300


def _is_auth_rate_limited(chat_id) -> bool:
    now = time.time()
    key = str(chat_id)
    failures = [ts for ts in _auth_failures.get(key, []) if now - ts < AUTH_LOCKOUT_SECONDS]
    _auth_failures[key] = failures
    return len(failures) >= AUTH_MAX_FAILURES


def _record_auth_failure(chat_id):
    now = time.time()
    key = str(chat_id)
    failures = [ts for ts in _auth_failures.get(key, []) if now - ts < AUTH_LOCKOUT_SECONDS]
    failures.append(now)
    _auth_failures[key] = failures


def generateServerAddr(app):
    try:
        if config[app]["server"]["ssl"]:
            http = "https://"
        else:
            http = "http://"
        try:
            addr = config[app]["server"]["addr"]
            port = config[app]["server"]["port"]
            path = config[app]["server"]["path"]
            return http + addr + ":" + str(port) + path
        except Exception:
            logger.warning("No ip or port defined.")
    except Exception as e:
        logger.warning(f"Generate of serveraddress failed: {e}.")


def cleanUrl(text):
    url = text.replace(" ", "%20")
    return url


def generateApiQuery(app, endpoint, parameters={}):
    try:
        endpoint_str = str(endpoint)
        if ".." in endpoint_str or any(c in endpoint_str for c in ("?", "#", "&", "\\")):
            raise ValueError("Invalid API endpoint")
        apikey = config[app]["auth"]["apikey"]
        url = (
            generateServerAddr(app) + "api/v3/" + endpoint_str + "?apikey=" + quote(str(apikey), safe="")
        )
        # If parameters exist iterate through dict and URL-encode parameters safely
        if parameters:
            for key, value in parameters.items():
                safe_key = quote(str(key), safe="")
                safe_val = quote(str(value), safe=":")
                url += "&" + safe_key + "=" + safe_val
        return cleanUrl(url)
    except Exception as e:
        logger.warning(f"Generate of APIQUERY failed: {e}.")


# Check if Id is authenticated
def checkId(update):
    if not os.path.exists(CHATID_PATH):
        return False
    target_id = str(update.effective_message.chat_id).strip()
    with open(CHATID_PATH, "r", encoding="utf8") as file:
        for line in file:
            chatId = line.strip("\n").split(" - ")[0].strip()
            if chatId and chatId == target_id:
                return True
    return False


async def authentication(update, context):
    if config.get("enableAllowlist") and not checkAllowed(update, "regular"):
        # When using this mode, bot will remain silent if user is not in the allowlist.txt
        logger.info("Allowlist is enabled, but userID isn't added into 'allowlist.txt'. So bot stays silent")
        return ConversationHandler.END

    chatid = update.effective_message.chat_id
    if checkId(update):
        await context.bot.send_message(
            chat_id=chatid,
            text=i18n.t("addarr.Chatid already allowed"),
        )
        return ConversationHandler.END

    if _is_auth_rate_limited(chatid):
        logger.warning(f"Rate-limited authentication attempt from chat_id={chatid}")
        await context.bot.send_message(
            chat_id=chatid, text=i18n.t("addarr.Wrong password")
        )
        return ConversationHandler.END

    password = update.message.text or ""
    if password.startswith("/auth "):
        password = password[len("/auth "):]
    elif "/auth " in password:
        password = password.replace("/auth ", "")

    configured_password = config.get("telegram", {}).get("password")
    if (
        configured_password is not None
        and str(configured_password) != ""
        and hmac.compare_digest(str(password), str(configured_password))
    ):
        with open(CHATID_PATH, "a", encoding="utf8") as file:
            file.write(await getChatName(context, chatid))
        await context.bot.send_message(
            chat_id=chatid,
            text=i18n.t("addarr.Chatid added"),
        )
        return "added"
    else:
        _record_auth_failure(chatid)
        from_user = getattr(update.message, "from_user", None)
        uname = getattr(from_user, "username", None) or getattr(from_user, "id", "unknown")
        logger.warning(f"Failed authentication attempt by [{uname}] (chat_id={chatid})")
        await context.bot.send_message(
            chat_id=chatid, text=i18n.t("addarr.Wrong password")
        )
        return ConversationHandler.END  # This only stops the auth conv, so it goes back to choosing screen


async def getChatName(context, chatid):
    chat = await context.bot.get_chat(chatid)
    if chat.username:
        chatName = str(chat.username)
    elif chat.title:
        chatName = str(chat.title)
    elif chat.last_name and chat.first_name:
        chatName = str(chat.last_name) + str(chat.first_name)
    elif chat.first_name:
        chatName = str(chat.first_name)
    elif chat.last_name:
        chatName = str(chat.last_name)
    else:
        chatName = None

    if chatName is not None:
        chatAuth = str(chatid) + " - " + str(chatName) + "\n"
    else:
        chatAuth = str(chatid) + "\n"
    return chatAuth


# Check if user is an admin or an allowed user
def checkAllowed(update, mode):
    if mode == "admin":
        path = ADMIN_PATH
    else:
        path = ALLOWLIST_PATH
    if not os.path.exists(path):
        return False
    user = update.effective_user
    if user is None:
        return False
    try:
        uid = user["id"]
    except Exception:
        uid = getattr(user, "id", None)
    try:
        uname = user["username"]
    except Exception:
        uname = getattr(user, "username", None)

    user_id_str = str(uid).strip() if uid is not None else ""
    username_str = str(uname).strip() if uname and str(uname).strip() != "None" else ""

    with open(path, "r", encoding="utf8") as file:
        for line in file:
            chatId = line.strip("\n").split(" - ")[0].strip()
            if not chatId:
                continue
            if (user_id_str and chatId == user_id_str) or (username_str and chatId == username_str):
                return True
    return False


def format_bytes(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def format_long_list_message(items):
    if not items:
        return ""
    string = ""
    for item in items:
        string += "• " \
                  + str(item["title"]) \
                  + " (" \
                  + str(item["year"]) \
                  + ")" \
                  + "\n" \
                  + "        status: " \
                  + str(item["status"]) \
                  + "\n" \
                  + "        monitored: " \
                  + str(item["monitored"]).lower() \
                  + "\n"

    # max length of a message is 4096 chars
    if len(string) <= 4096:
        return string

    stringParts = []
    remaining = string
    while len(remaining) > 4096:
        split_idx = remaining.rfind("\n", 0, 4096)
        if split_idx <= 0:
            split_idx = 4096
        stringParts.append(remaining[:split_idx])
        remaining = remaining[split_idx:].lstrip("\n")
    if remaining:
        stringParts.append(remaining)
    return stringParts


def getAuthChats():
    chats = []
    if not os.path.exists(CHATID_PATH):
        return chats
    with open(CHATID_PATH, "r", encoding="utf8") as file:
        for line in file:
            cid = line.strip("\n").split(" - ")[0].strip()
            if cid:
                chats.append(cid)
    return chats

