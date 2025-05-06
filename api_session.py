import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config_manager import config

logger = logging.getLogger(__name__)


def create_session():
    """Creates a requests session with retry and proxy support."""
    session = requests.Session()

    # Retry strategy
    retry = Retry(
        total=5,  # Maximum number of retries
        backoff_factor=0.5,  # Exponential backoff factor (sleep longer between retries)
        status_forcelist=[500, 502, 503, 504],  # HTTP status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Proxy configuration
    if config.getboolean("Proxy", "use_proxy"):
        proxies = {"http": config["Proxy"]["http"], "https": config["Proxy"]["https"]}
        session.proxies.update(proxies)
        logger.info(f"Using proxy: {proxies}")
    else:
        logger.info("Not using a proxy.")

    return session
