import os
import yaml

from definitions import CONFIG_PATH, CONFIG_EXAMPLE_PATH, DEFAULT_SETTINGS

if os.path.exists(CONFIG_PATH):
    config = yaml.safe_load(open(CONFIG_PATH, encoding="utf8")) or {}
else:
    config = yaml.safe_load(open(CONFIG_EXAMPLE_PATH, encoding="utf8")) or {}
config_example = yaml.safe_load(open(CONFIG_EXAMPLE_PATH, encoding="utf8")) or {}


for setting, default_value in DEFAULT_SETTINGS.items():
    if setting not in config:
        config[setting] = default_value


def flatten_dict(dd, separator ='/', prefix =''):
    return { prefix + separator + k if prefix else k : v
             for kk, vv in dd.items()
             for k, v in flatten_dict(vv, separator, kk).items()
             } if isinstance(dd, dict) else { prefix : dd }


def checkConfig():
    missingConfig=[]
    for key_ex, value_ex in flatten_dict(config_example).items():
        if key_ex.startswith("miniapp/"):
            if not config.get("miniapp", {}).get("enable", False):
                continue
            if key_ex == "miniapp/databaseURL" and not config.get("miniapp", {}).get("databaseURL"):
                missingConfig.append(key_ex)
            continue
        if key_ex not in flatten_dict(config):
            missingConfig.append(key_ex)
    return missingConfig


def checkConfigValues():
    wrongValues = []
    languages = ["de-de", "en-us", "es-es", "fr-fr", "it-it", "nl-be", "pl-pl", "pt-pt", "ru-ru"]
    if config.get("language") not in languages:
        wrongValues.append("language")
    if config.get("miniapp", {}).get("enable", False):
        if not config["miniapp"].get("databaseURL"):
            wrongValues.append("miniapp/databaseURL")
    return wrongValues

