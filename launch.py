import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
hf_backup_tool_dir = os.path.join(current_dir, "hf_backup_tool")

if __name__ == "__main__":
    sys.path.insert(0, hf_backup_tool_dir)
    from main import start_application
    exit_code = start_application()
    sys.exit(exit_code)
