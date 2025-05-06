import configparser
import os
import logging
from custom_exceptions import ConfigError  # Import ConfigError

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config_path = "config.ini"

# Default config
config["HuggingFace"] = {
    "api_token": "",  # Store obfuscated API token
    "rate_limit_delay": "1",  # Delay in seconds between API calls
    "org": "",  # Store org or user
    "repo": "",  # Store repo name
}

config["Zip"] = {"default_zip_name": "my_archive"}

config["Proxy"] = {
    "use_proxy": "False",  # Whether to use a proxy server
    "http": "",  # HTTP proxy URL
    "https": "",  # HTTPS proxy URL
}


def load_config():
    """Loads the configuration from the config file."""
    logger.info("Loading configuration...")
    if os.path.exists(config_path):
        logger.info(f"Configuration file found: {config_path}")
        try:
            config.read(config_path)
            logger.info(f"Configuration loaded successfully.")
            # *** DEBUGGING ***
            logger.debug(f"Config contents after loading: {config.items()}")

        except Exception as e:
            logger.error(f"Error reading configuration file: {e}", exc_info=True)
            logger.warning("Creating default configuration.")
            try:
                save_config()  # Create a new default config
                logger.info("Default configuration created after load failure.")
            except ConfigError as save_error:
                logger.error(
                    f"Failed to create default config after load failure: {save_error}",
                    exc_info=True,
                )
                raise ConfigError(
                    "Failed to load or create default configuration."
                ) from save_error
            raise ConfigError(
                f"Failed to load configuration from {config_path}: {e}"
            ) from e  # Raise the config error
    else:
        logger.warning(
            f"Configuration file not found: {config_path}. Creating default config."
        )
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
    """Saves the configuration to the config file."""
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
        ) from e  # Raise the config error


config = load_config()