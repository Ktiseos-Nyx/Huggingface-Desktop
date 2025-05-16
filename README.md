[![Made with Python](https://img.shields.io/badge/Python->=3.10-blue?logo=python&logoColor=white)](https://python.org "Go to Python homepage") [![CodeQL](https://github.com/Ktiseos-Nyx/Huggingface-Desktop/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/Ktiseos-Nyx/Huggingface-Desktop/actions/workflows/github-code-scanning/codeql) ![Discord](https://img.shields.io/discord/1330470680348594276?style=social&logo=discord&logoColor=%235865F2) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

# Hugging Face Backup Tool

A user-friendly desktop application for backing up your Hugging Face models, datasets, and spaces.

[Connect with us on Discord](https://discord.gg/MASBKnNFWh)

## Table of Contents

1.  [Overview](#overview)
2.  [Features](#features)
3.  [Installation](#installation)
    *   [3.1. System Requirements (Theoretical)](#31-system-requirements-theoretical)
    *   [3.2. Installation Steps](#32-installation-steps)
4.  [Configuration](#configuration)
5.  [Issues & Known Limitations](#issues--known-limitations)
6.  [Usage](#usage)
7.  [Contributing](#contributing)
8.  [License](#license)
9.  [![view - Documentation](https://img.shields.io/badge/view-Documentation-blue?style=for-the-badge)](/docs/ "Go to project documentation")
10.  [![contributions - welcome](https://img.shields.io/badge/contributions-welcome-blue)](/CONTRIBUTING.md "Go to contributions doc") 

## 1. Overview

This tool provides a graphical user interface (GUI) to simplify backing up your local machine's files to the Hugging Face Hub. It's designed to be a more intuitive alternative to using the command-line interface (CLI).

*   **Upload Files and Folders:** Easily back up your local models, datasets, and spaces to the Hugging Face Hub.
*   **Manage Repositories:** Organize your backups into different repositories.
*   **Configure Settings:** Configure your API token, proxy settings, and rate limit delay, all within the application.

<details>
<summary>Preview</summary>
<p align="center"><img width="1052" alt="Screenshot 2025-05-07 at 16 35 11" src="https://github.com/user-attachments/assets/09623bc9-4045-48b5-8f83-ffdeacc87d4c" />

  
</p>
</details>

**Why use this tool instead of the command line?**

> The Hugging Face Hub CLI is powerful, but it can be intimidating for users unfamiliar with the command line. This tool offers a more visual and intuitive approach to managing your Hugging Face backups, making it more accessible.

## 2. Features

Here's a quick overview of what you can do with the Hugging Face Backup Tool:

*   **Hugging Face Uploader:**  Upload files and entire folders to the Hugging Face Hub.
*   **Zip Folder:** Create ZIP archives of your local folders for backup.
*   **Download:** Download files from the Hugging Face Hub.
*   **Material Themes:** Customize the application's appearance with a variety of beautiful Qt Material themes.

## 3. Installation

This section guides you through installing and setting up the tool. It requires **Python 3.10 or higher**.

### 3.1. System Requirements (Theoretical)

The Hugging Face Backup Tool is built using PyQt6, a cross-platform GUI framework. This means it *should* be compatible with the following operating systems:

*   **Windows:** Windows 10 or later (64-bit)
*   **macOS:** macOS 10.14 (Mojave) or later
*   **Linux:** Most modern Linux distributions (e.g., Ubuntu, Fedora, Debian)

> **Important Note:** While the tool *should* work on these operating systems, it has only been tested on [MacOS Ventura 13.5.1]. Your experience may vary. Please report any compatibility issues you encounter!

### 3.2. Installation Steps

Here are the general steps for installing the tool.

**Steps:**

1.  **Install Python:** Make sure you have Python 3.10 or higher installed.  You can download it from the official Python website ([https://www.python.org/downloads/](https://www.python.org/downloads/)) or your operating system's package manager.

    *   **Windows:**  During installation, make sure to check the box "Add Python to PATH".
    *   **Linux:**  Use your distribution's package manager (e.g., `sudo apt install python3` on Debian/Ubuntu, `sudo dnf install python3` on Fedora/CentOS/RHEL).
    *   **macOS:** You may install with Homebrew (`brew install python@3.10`) but you may also install from the website.

2.  **Clone the Repository:**  Open a terminal or command prompt and clone the repository:

    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd [YOUR_REPOSITORY_DIRECTORY]
    ```

    > Replace `[YOUR_REPOSITORY_URL]` with the URL of your GitHub repository and `[YOUR_REPOSITORY_DIRECTORY]` with the desired directory name.

3.  **Create a Virtual Environment (Recommended):**  It's best practice to use a virtual environment.  This isolates the project's dependencies.

    ```bash
    python -m venv venv
    ```

4.  **Activate the Virtual Environment:**

    *   **Windows:**

        ```cmd
        venv\Scripts\activate
        ```

    *   **Linux/macOS (Bash/Zsh):**

        ```bash
        source venv/bin/activate
        ```

    *   **FISH:**

        ```fish
        source venv/bin/activate.fish
        ```

5.  **Install Dependencies:**  Install the required Python packages using `pip`:

    ```bash
    pip install -r requirements.txt
    ```
 
6.  **Run the Application:**

    ```bash
    python launch.py
    ```

## 4. Configuration

Before using the tool, you need to configure it with your Hugging Face API token.

**Steps:**

1.  **Get an API Token:** If you don't have one, create a Hugging Face API token with "write" access.  You can do this in your Hugging Face account settings:  ([https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
2.  **Open the Configuration Dialog:** Click the "Edit Config (API Token)" button within the application.
3.  **Enter Your Token:** Paste your API token into the "Hugging Face API Token" field.
4.  **Save the Configuration:** Click the "Save" button.

## 5. Issues & Known Limitations

> This section lists some of the known limitations and areas for improvement.

*   **Single File Upload (Currently):** The tool currently only supports uploading *one* file at a time.
*   **Output Logging:**  Output and progress updates may currently be visible only in the terminal logs.
*   **Repository Creation (Potential Issues):**  Creating a new repository might still have issues.  It's generally recommended to pre-create your repositories on the Hugging Face Hub.
*   **Spacing and UI Glitches:**  There might still be some spacing or UI layout issues.
*   **Multiple File Upload:** The GUI doesn't support multiple file uploads yet.
*   **macOS Development Challenges:** Developing on macOS can be tricky (as you noted!).

## 6. Usage

Here's how to use the Hugging Face Backup Tool:

**Steps:**

1.  **Select a Directory:**  Click the "Select Directory" button, and choose the directory containing the files you want to back up.
2.  **Choose a File Type:**  Use the "File Type" dropdown to select the type of files you want to upload (e.g., SafeTensors, PyTorch Models).
3.  **Select Files:**  The file list will populate.  Select the files to upload.
4.  **Enter Repository Information:**  Fill in the "Owner" (your organization or username) and "Repository" name.
5.  **Click "Upload":** Start the upload process.
6.  **Check Output:** Check the output window in the GUI for progress updates.

## 7. Contributing

Contributions are very welcome! If you'd like to contribute, please:

*   Submit pull requests with your improvements or bug fixes.
*   Open issues to report bugs, request features, or suggest improvements.

## 8. License

This project is licensed under the GNU General Public License v3.0.  See the [LICENSE](https://github.com/Ktiseos-Nyx/Huggingface-Desktop#GPL-3.0-1-ov-file) file for details.

> **GNU General Public License v3.0:** ([https://www.gnu.org/licenses/gpl-3.0.en.html](https://www.gnu.org/licenses/gpl-3.0.en.html)).
