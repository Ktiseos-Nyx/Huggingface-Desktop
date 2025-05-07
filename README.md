# Hugging Face Backup Tool

A user-friendly desktop application for backing up your Hugging Face models, datasets, and spaces. This is in progress so some things may not be working 100% quite yet.

[TOC]

## Overview

This tool provides a graphical user interface (GUI) for interacting with the Hugging Face Hub, making it easier to:

*   **Upload files and folders:** Quickly back up your local models, datasets, and spaces to the Hugging Face Hub.
*   **Manage repositories:** Organize your backups into different repositories.
*   **Configure settings:** Easily set your API token, proxy settings, and rate limit delay.

<details>

<summary>Image, Video & Ascii Terminal Views</summary>

### Image & Overview Preview

<img width="803" alt="Screenshot 2025-05-06 at 11 28 13" src="https://github.com/user-attachments/assets/aaad7468-3fa3-4c68-93c1-21b2cf09ff8e" />

#### Video
https://github.com/user-attachments/assets/67105f33-4f13-438e-91b3-f029b9e80066

#### Ascii Cast
![718285](https://github.com/user-attachments/assets/8ccf5fb2-c36f-4e28-995e-6bb1b80886eb)

See the recording on [asciinema.org](https://asciinema.org/a/O3X0ubf8j9ZClIfZKas25mkSp).
</details>

**Why use this tool instead of the command line?**

While the Hugging Face Hub command-line interface (CLI) is powerful, it can be intimidating for users who are not comfortable with the command line. This tool offers a more intuitive and visual way to manage your Hugging Face backups, making it accessible to a wider audience.

## Features

*   **Hugging Face Uploader:** Upload files and folders to the Hugging Face Hub with ease.
*   **Zip Folder:** Create zip archives of your local folders.
*   **Download:** Download files from the Hugging Face Hub.
*   **Material Themes:** Customize the look and feel of the application with a variety of beautiful Qt Material themes.

## Installation

This tool requires **Python 3.10 or higher**. You can install it using either [UV](https://astral.sh/blog/uv) (recommended for faster installation) or the standard `pip` package installer.

### Compatible Operating Systems (Theoretical)

This tool is built using PyQt6, which is a cross-platform GUI framework. Therefore, it should theoretically be compatible with the following operating systems:

*   **Windows:** Windows 10 or later (64-bit)
*   **macOS:** macOS 10.14 (Mojave) or later
*   **Linux:** Most modern Linux distributions (e.g., Ubuntu, Fedora, Debian)

**Note:** While the tool *should* work on these operating systems, it has only been tested on [MacOS Ventura 13.5.1]. Your experience may vary. Please report any compatibility issues you encounter.

### Installation with UV (Recommended)

[UV](https://astral.sh/blog/uv) is a blazingly fast Python package installer and resolver. It's designed to be a drop-in replacement for `pip` and offers significant performance improvements.

**1. Prerequisites:**

*   **Python 3.10 or higher:** Make sure you have Python installed on your system.
*   **UV:** Install UV using pip:

    ```bash
    pip install uv
    ```

**2. Clone the Repository:**

    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd [YOUR_REPOSITORY_DIRECTORY]
    ```

    Replace `[YOUR_REPOSITORY_URL]` with the URL of your GitHub repository and `[YOUR_REPOSITORY_DIRECTORY]` with the name of the directory you cloned into.

**3. Create a Virtual Environment:**

    It's highly recommended to use a virtual environment to isolate the project's dependencies.

    ```bash
    python -m venv .venv
    ```

**4. Activate the Virtual Environment:**

    *   **Bash/Zsh:**

        ```bash
        source .venv/bin/activate
        ```

    *   **FISH:**

        ```fish
        source .venv/bin/activate.fish
        ```

        **Important for FISH users:** UV doesn't directly support `activate.fish`. You may need to manually add the virtual environment's `bin` directory to your `PATH` in your `~/.config/fish/config.fish` file:

        ```fish
        set -U fish_user_paths .venv/bin $fish_user_paths
        ```

        Then, restart your FISH terminal or run `source ~/.config/fish/config.fish`.

**5. Install Dependencies with UV:**

    ```bash
    uv pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt` file, you can install the dependencies directly:

    ```bash
    uv pip install PyQt6 qt_material huggingface_hub requests
    ```

### Installation with Pip (Alternative)

If you prefer to use the standard `pip` package installer, you can follow these steps:

**1. Prerequisites:**

*   **Python 3.10 or higher:** Make sure you have Python installed on your system.

**2. Clone the Repository:**

    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd [YOUR_REPOSITORY_DIRECTORY]
    ```

    Replace `[YOUR_REPOSITORY_URL]` with the URL of your GitHub repository and `[YOUR_REPOSITORY_DIRECTORY]` with the name of the directory you cloned into.

**3. Create a Virtual Environment:**

    It's highly recommended to use a virtual environment to isolate the project's dependencies.

    ```bash
    python -m venv .venv
    ```

**4. Activate the Virtual Environment:**

    *   **Bash/Zsh:**

        ```bash
        source .venv/bin/activate
        ```

    *   **FISH:**

        ```fish
        source .venv/bin/activate.fish
        ```

        **Important for FISH users:** You may need to manually add the virtual environment's `bin` directory to your `PATH` in your `~/.config/fish/config.fish` file:

        ```fish
        set -U fish_user_paths .venv/bin $fish_user_paths
        ```

        Then, restart your FISH terminal or run `source ~/.config/fish/config.fish`.

**5. Install Dependencies with Pip:**

    ```bash
    pip install -r requirements.txt
    ```

    If you don't have a `requirements.txt` file, you can install the dependencies directly:

    ```bash
    pip install PyQt6 qt_material huggingface_hub requests
    ```

**Required Packages:**

The following packages are required to run this tool:

*   `PyQt6`
*   `qt_material`
*   `huggingface_hub`
*   `requests`

**6. Run the Application:**

    ```bash
    python hf_backup_tool/main.py
    ```

## Configuration

1.  **API Token:** You'll need a Hugging Face API token with "write" access. You can create one in your Hugging Face account settings ([https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)).
2.  **Open the Configuration Dialog:** Click the "Edit Config (API Token)" button in the application.
3.  **Enter Your API Token:** Paste your API token into the "Hugging Face API Token" field.
4.  **Save the Configuration:** Click the "Save" button.

## Usage

1.  **Select a Directory:** Choose the directory containing the files you want to back up.
2.  **Choose a File Type:** Select the type of files you want to upload (e.g., SafeTensors, PyTorch Models).
3.  **Select Files:** Select the files you want to upload from the list.
4.  **Enter Repository Information:** Enter the owner (organization or username) and repository name.
5.  **Click "Upload":** Start the upload process.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

**A copy of the GNU General Public License v3.0 can be found at [https://www.gnu.org/licenses/gpl-3.0.en.html](https://www.gnu.org/licenses/gpl-3.0.en.html).**
