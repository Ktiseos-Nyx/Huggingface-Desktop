import configparser
import os
import logging
from custom_exceptions import ConfigError
from hf_backup_tool.token_utils import obfuscate_token, deobfuscate_token

logger = logging.getLogger(__name__)
config = configparser.ConfigParser()
config_path = os.path.expanduser("~/.huggingface_uploader_config.ini")
DEFAULT_CONFIG = {
    "HuggingFace": {
        "api_token": "",
        "rate_limit_delay": "1",
        "org": "",
        "repo": "",
    },
    "Zip": {"default_zip_name": "my_archive"},
    "Proxy": {
        "use_proxy": "False",
        "http": "",
        "https": "",
    },
    "DownloadQueue": {
        "max_concurrent_downloads": "1",
        "auto_clear_completed_downloads": "True"
    },
    "UploadQueue": {
        "max_concurrent_upload_jobs": "1",
        "auto_clear_completed_uploads": "True"
    },
    "Window": { # NEW Section
        "width": "700",
        "height": "550",
    }
}

def load_config():
    logger.info("Loading configuration...")
    if os.path.exists(config_path):
        logger.info(f"Configuration file found: {config_path}")
        try:
            config.read(config_path)
            logger.info("Configuration loaded successfully.")
            logger.debug(f"Config contents after loading: {config.items()}")
        except Exception as e:
            logger.error(f"Error reading configuration file: {e}", exc_info=True)
            raise ConfigError(
                f"Failed to load configuration from {config_path}: {e}"
            ) from e
    else:
        logger.warning(
            f"Configuration file not found: {config_path}. Creating default config."
        )
        config.read_dict(DEFAULT_CONFIG)
        try:
            save_config()
            logger.info(f"Default configuration created: {config_path}")
        except ConfigError as save_error:
            logger.error(
                f"Failed to create default config: {save_error}", exc_info=True
            )
            raise ConfigError("Failed to create default configuration.") from save_error
    return config

def save_config():
    logger.info("Saving configuration...")
    try:
        with open(config_path, "w") as configfile:
            config.write(configfile)
        logger.info("Configuration saved successfully.")
        logger.debug(f"Config contents after saving: {config.items()}")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        raise ConfigError(
            f"Failed to save configuration to {config_path}: {e}"
        ) from e

# Add these to config_manager.py
def get_window_width():
    return int(config.get("Window", "width", fallback="700"))

def get_window_height():
    return int(config.get("Window", "height", fallback="550"))
def set_window_size(width: int, height: int):
    if not config.has_section("Window"):
        config.add_section("Window")
    config.set("Window", "width", str(width))
    config.set("Window", "height", str(height))
    save_config()
def get_api_token():
    clear_token_from_env = os.environ.get("HF_API_TOKEN")
    if clear_token_from_env:
        logger.debug("Using API token from HF_API_TOKEN environment variable.")
        return clear_token_from_env
    
    obfuscated_token_from_config = config.get("HuggingFace", "api_token", fallback="")
    if obfuscated_token_from_config:
        logger.debug("Found API token in config, deobfuscating.")
        return deobfuscate_token(obfuscated_token_from_config)
    
    logger.debug("No API token found in environment or config.")
    return None # <---- CHANGE THIS LINE to None

def set_api_token(token):
    if not config.has_section("HuggingFace"):
        config.add_section("HuggingFace")
    obfuscated_api_token = obfuscate_token(token)
    config.set("HuggingFace", "api_token", obfuscated_api_token)
    save_config()

def get_rate_limit_delay():
    return float(config.get("HuggingFace", "rate_limit_delay", fallback="1"))

def set_rate_limit_delay(delay):
    if not config.has_section("HuggingFace"):
        config.add_section("HuggingFace")
    config.set("HuggingFace", "rate_limit_delay", str(delay))
    save_config()

def set_proxy(proxy_settings):
    if not config.has_section("Proxy"):
        config.add_section("Proxy")
    config.set("Proxy", "use_proxy", proxy_settings.get("use_proxy", "False"))
    config.set("Proxy", "http", proxy_settings.get("http", ""))
    config.set("Proxy", "https", proxy_settings.get("https", ""))
    save_config()

def get_proxy():
    return {
        "use_proxy": config.get("Proxy", "use_proxy", fallback="False"),
        "http": config.get("Proxy", "http", fallback=""),
        "https": config.get("Proxy", "https", fallback=""),
    }

def get_max_concurrent_downloads():
    return int(config.get("DownloadQueue", "max_concurrent_downloads", fallback="1"))

def set_max_concurrent_downloads(max_downloads):
    if not config.has_section("DownloadQueue"):
        config.add_section("DownloadQueue")
    config.set("DownloadQueue", "max_concurrent_downloads", str(max_downloads))
    save_config()

def get_auto_clear_completed_downloads():
    return config.getboolean("DownloadQueue", "auto_clear_completed_downloads", fallback=True)

def set_auto_clear_completed_downloads(auto_clear):
    if not config.has_section("DownloadQueue"):
        config.add_section("DownloadQueue")
    config.set("DownloadQueue", "auto_clear_completed_downloads", str(auto_clear))
    save_config()

def get_max_concurrent_upload_jobs():
    return int(config.get("UploadQueue", "max_concurrent_upload_jobs", fallback="1"))

def set_max_concurrent_upload_jobs(max_jobs):
    if not config.has_section("UploadQueue"):
        config.add_section("UploadQueue")
    config.set("UploadQueue", "max_concurrent_upload_jobs", str(max_jobs))
    save_config()

def get_auto_clear_completed_uploads():
    return config.getboolean("UploadQueue", "auto_clear_completed_uploads", fallback=True)

def set_auto_clear_completed_uploads(auto_clear):
    if not config.has_section("UploadQueue"):
        config.add_section("UploadQueue")
    config.set("UploadQueue", "auto_clear_completed_uploads", str(auto_clear))
    save_config()
try:
    load_config()
except ConfigError as e:
    logger.error(f"Initial config load failed: {e}")
