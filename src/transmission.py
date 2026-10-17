import subprocess

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from commons import authentication, checkAllowed, checkId
from config import config as root_config
from translations import i18n
import logging
import logger

# Set up logging
logLevel = logging.DEBUG if root_config.get("debugLogging", False) else logging.INFO
logger = logger.getLogger("addarr.radarr", logLevel, root_config.get("logToConsole", False))

config = root_config["transmission"]

TSL_LIMIT, TSL_NORMAL = range(2)


async def transmission(update, context):
    if root_config.get("enableAllowlist") and not checkAllowed(update, "regular"):
        # When using this mode, bot will remain silent if user is not in the allowlist.txt
        logger.info("Allowlist is enabled, but userID isn't added into 'allowlist.txt'. So bot stays silent")
        return ConversationHandler.END

    if not config["enable"]:
        await context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text=i18n.t("addarr.Transmission.NotEnabled"),
        )
        return ConversationHandler.END

    if not checkId(update):
        await context.bot.send_message(
            chat_id=update.effective_message.chat_id, text=i18n.t("addarr.Authorize")
        )
        return ConversationHandler.END

    if config.get("onlyAdmin") and not checkAllowed(update, "admin"):
        await context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text=i18n.t("addarr.NotAdmin"),
        )
        return ConversationHandler.END

    keyboard = [[
        InlineKeyboardButton(
            '\U0001F40C ' + i18n.t("addarr.Transmission.TSL"),
            callback_data=str(TSL_LIMIT)
        ),
        InlineKeyboardButton(
            '\U0001F406 ' + i18n.t("addarr.Transmission.Normal"),
            callback_data=str(TSL_NORMAL)
        ),
    ]]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        i18n.t("addarr.Transmission.Speed"), reply_markup=markup
    )
    return TSL_NORMAL


async def changeSpeedTransmission(update, context):
    if not checkId(update):
        if (
            await authentication(update, context) == "added"
        ):  # To also stop the beginning command
            return ConversationHandler.END
        return ConversationHandler.END

    if config.get("onlyAdmin") and not checkAllowed(update, "admin"):
        await context.bot.send_message(
            chat_id=update.effective_message.chat_id,
            text=i18n.t("addarr.NotAdmin"),
        )
        return ConversationHandler.END

    choice = str(update.callback_query.data)
    cmd = ["transmission-remote", str(config["host"])]
    if config.get("authentication"):
        cmd.extend(["--auth", f"{config['username']}:{config['password']}"])

    if choice == str(TSL_NORMAL):
        cmd.append("--no-alt-speed")
        message = i18n.t("addarr.Transmission.ChangedToNormal")
    elif choice == str(TSL_LIMIT):
        cmd.append("--alt-speed")
        message = i18n.t("addarr.Transmission.ChangedToTSL")
    else:
        return ConversationHandler.END

    subprocess.run(cmd, check=False, timeout=15)

    await context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=message,
    )
    return ConversationHandler.END

