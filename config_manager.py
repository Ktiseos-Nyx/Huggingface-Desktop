# config_manager.py
import configparser
import os
import logging
from custom_exceptions import ConfigError  # Import ConfigError

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config_path = os.path.expanduser("~/.huggingface_uploader_config.ini")

DEFAULT_CONFIG = {
     "HuggingFace": {
         "api_token": "",  # Store obfuscated API token
         "rate_limit_delay": "1",  # Delay in seconds between API calls
         "org": "",  # Store org or user
         "repo": "",  # Store repo name
     },
     "Zip": {"default_zip_name": "my_archive"},
     "Proxy": {
         "use_proxy": "False",  # Whether to use a proxy server
         "http": "",  # HTTP proxy URL
         "https": "",  # HTTPS proxy URL
     },
}

def load_config():
    """Loads the configuration from the config file.

    If the config file does not exist, it creates a default config.
    Raises ConfigError if the config can't be loaded.
    """
    logger.info("Loading configuration...")
    if os.path.exists(config_path):
        logger.info(f"Configuration file found: {config_path}")
        try:
            config.read(config_path)
            logger.info("Configuration loaded successfully.")
            # *** DEBUGGING ***
            logger.debug(f"Config contents after loading: {config.items()}")

        except Exception as e:
            logger.error(f"Error reading configuration file: {e}", exc_info=True)
            raise ConfigError(
                f"Failed to load configuration from {config_path}: {e}"
            ) from e  # Re-raise config error
    else:
        logger.warning(
            f"Configuration file not found: {config_path}. Creating default config."
        )
        config.read_dict(DEFAULT_CONFIG)  # Apply default config
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
    """Saves the configuration to the config file.

    Raises ConfigError on failure.
    """
    logger.info("Saving configuration...")
    try:
        with open(config_path, "w") as configfile:
            config.write(configfile)
        logger.info("Configuration saved successfully.")
        # *** DEBUGGING ***
        logger.debug(f"Config contents after saving: {config.items()}")
        return True  # Indicate success
    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        raise ConfigError(
            f"Failed to save configuration to {config_path}: {e}"
        ) from e  # Re-raise the config error

# --- Convenience methods ---
def get_api_token():
    """Gets the Hugging Face API token from the configuration."""
    if token := os.environ.get("HF_API_TOKEN"):
        return token
    return config.get("HuggingFace", "api_token") # Corrected - Removed the extra default argument ""

def set_api_token(token):
    """Sets the Hugging Face API token in the configuration."""
    config.set("HuggingFace", "api_token", token)
    save_config()

def get_rate_limit_delay():
    """Gets the rate limit delay in seconds."""
    return float(config.get("HuggingFace", "rate_limit_delay", fallback="1"))

def set_rate_limit_delay(delay):
    """Sets the rate limit delay in seconds."""
    config.set("HuggingFace", "rate_limit_delay", str(delay)) # Save as string
    save_config()

def set_proxy(proxy_settings):
    """Sets proxy settings in the configuration."""
    config.set("Proxy", "use_proxy", proxy_settings.get("use_proxy", "False"))
    config.set("Proxy", "http", proxy_settings.get("http", ""))
    config.set("Proxy", "https", proxy_settings.get("https", ""))
    save_config()  # save the config

def get_proxy():
    """Gets the proxy settings from the configuration."""
    return {
        "use_proxy": config.get("Proxy", "use_proxy", fallback="False"),
        "http": config.get("Proxy", "http", fallback=""),
        "https": config.get("Proxy", "https", fallback=""),
    }
# --- Load the configuration when the module is imported ---
try:
    load_config()  # Load config when module is imported
except ConfigError as e:
    logger.error(f"Initial config load failed: {e}")