import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config_manager import config

logger = logging.getLogger(__name__)

def create_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if config.getboolean("Proxy", "use_proxy"):
        proxies = {"http": config["Proxy"]["http"], "https": config["Proxy"]["https"]}
        session.proxies.update(proxies)
        logger.info(f"Using proxy: {proxies}")
    else:
        logger.info("Not using a proxy.")
    return session
