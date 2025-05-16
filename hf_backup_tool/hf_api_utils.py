# hf_api_utils.py
import logging
from huggingface_hub import HfApi, create_repo
from config_manager import get_api_token  # Import for token retrieval

logger = logging.getLogger(__name__)

def upload_file_to_hub(repo_id, file_path, filename_in_repo, repo_type="model", repo_folder="", commit_message="Upload from script", create_pr=False):
    """Uploads a file to the Hugging Face Hub."""
    token = get_api_token()
    if not token:
        logger.error("No API token found.")
        return False, "API token not found."

    try:
        api = HfApi()
        api.upload_file(
            path_or_fileobj=file_path,
            path_in_repo=filename_in_repo,
            repo_id=repo_id,
            repo_type=repo_type,
            token=token,
            commit_message=commit_message,
            create_pr=create_pr,
        )
        logger.info(f"Successfully uploaded {filename_in_repo} to {repo_id}")
        return True, "File uploaded successfully."
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        return False, str(e)

def create_repo_on_hub(repo_id, repo_type="model"):
    """Creates a repository on the Hugging Face Hub."""
    token = get_api_token()
    if not token:
        logger.error("No API token found.")
        return False, "API token not found."

    try:
        create_repo(repo_id, token=token, repo_type=repo_type, exist_ok=True)
        logger.info(f"Successfully created or confirmed repository: {repo_id}")
        return True, "Repository created successfully."
    except Exception as e:
        logger.error(f"Error creating repository: {e}", exc_info=True)
        return False, str(e)

# Add other HF API functions as needed (e.g., to check repo existence)