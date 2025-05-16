import sys
import os
import subprocess
import importlib.util  # For checking if a module is installed

current_dir = os.path.dirname(os.path.abspath(__file__))
hf_backup_tool_dir = os.path.join(current_dir, "hf_backup_tool")

def install_missing_dependencies():
    """Installs missing dependencies from requirements.txt using pip."""
    try:
        with open(os.path.join(current_dir, "requirements.txt"), "r") as f:
            for line in f:
                package_name = line.strip()
                if package_name:  # Skip empty lines
                    if not is_module_installed(package_name):
                        print(f"Installing missing dependency: {package_name}")
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", package_name]
                        )
    except FileNotFoundError:
        print("Error: requirements.txt not found.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    return True

def is_module_installed(module_name):
    """Checks if a Python module is installed."""
    spec = importlib.util.find_spec(module_name)
    return spec is not None


if __name__ == "__main__":
    # Install missing dependencies before running the app
    if not install_missing_dependencies():
        sys.exit(1)  # Exit if installation failed

    sys.path.insert(0, hf_backup_tool_dir)
    from main import start_application
    exit_code = start_application()
    sys.exit(exit_code)