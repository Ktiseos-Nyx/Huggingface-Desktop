# Example usage
import logging
from api_session import APISession #  IMPORT the class

logger = logging.getLogger(__name__)

try:
    with APISession() as session:
        response = session.get("https://api.example.com/some_api_endpoint", timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        # Process the data
        print(data)

except requests.exceptions.RequestException as e:
    logger.error(f"Request failed: {e}")
    # Handle network errors, timeouts, etc.
except ValueError as e:
    logger.error(f"Error parsing JSON: {e}")
    # Handle JSON decoding errors
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")