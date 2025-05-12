import keyring
import logging

logger = logging.getLogger(__name__)
KEYRING_SERVICE_NAME = "huggingface_backup"

def get_api_token(alias):
    try:
        api_token = keyring.get_password(KEYRING_SERVICE_NAME, alias)
        if api_token:
            logger.info(f"Successfully retrieved API token for alias: {alias}")
            return api_token
        else:
            logger.warning(f"No API token found for alias: {alias}")
            return None
    except Exception as e:
        logger.error(
            f"Error retrieving API token for alias {alias}: {e}", exc_info=True
        )
        return None

def set_api_token(alias, token):
    try:
        keyring.set_password(KEYRING_SERVICE_NAME, alias, token)
        logger.info(f"Successfully stored API token for alias: {alias}")
    except Exception as e:
        logger.error(f"Error setting API token for alias {alias}: {e}", exc_info=True)

def delete_api_token(alias):
    try:
        keyring.delete_password(KEYRING_SERVICE_NAME, alias)
        logger.info(f"Successfully deleted API token for alias: {alias}")
    except Exception as e:
        logger.error(f"Error deleting API token for alias {alias}: {e}", exc_info=True)
