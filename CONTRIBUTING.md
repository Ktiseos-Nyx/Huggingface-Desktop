# Contributing to Hugging Face Backup Tool

Thank you for your interest in contributing to the Hugging Face Backup Tool! We welcome contributions from everyone, regardless of their experience level.

## About Ktiseos Nyx

Ktiseos Nyx is a space cultivated by Earth & Dusk Media, a name whispered from the echoes of Ktisis Hyperboreia, the level 87 dungeon in Final Fantasy XIV: Endwalker. Like the Ktiseos gear found within that ancient place, we see power and potential in what's often overlooked – a place where we are allowed to grow, experiment, and expand. We are a collective of coders, gamers, artists, and thinkers whose diverse experiences and perspectives shape the world around us. We believe that the most transformative ideas are born when we dare to stray from the well-worn paths.

Ktiseos Nyx is a refuge for those who value community, where the foundations we build are as important as the tools themselves. We don't aim to simply conform; we strive to create connections, push limits, and foster a sanctuary for the bold and brilliant. In the darkness, we find our strength; together, we craft a new dawn.

Our commitment to this vision extends to the very core of our process:

*   **Open and Collaborative:** Code within Ktiseos Nyx is a shared resource, a living testament to collaboration. We embrace diverse approaches to development, including the responsible use of advanced tools like Large Language Models. Our projects are generally licensed under the [GNU GPL v3.0 License](LICENSE), chosen for its copyleft provisions to encourage broad collaboration and reuse.
*   **Security Conscious:** We rigorously vet the packages and dependencies we use, prioritizing security and stability. While striving for user-friendliness in all our tools, we also challenge ourselves to anticipate future needs, both niche and widespread. We are committed to addressing security vulnerabilities promptly and transparently.
*   **Community Driven:** We operate transparently, with key decisions made collaboratively. We welcome contributions from everyone, regardless of skill level. Join the discussion on our [Discord Server](https://discord.gg/HhBSvM9gBY)!
*   **Respectful and Inclusive:** We are committed to maintaining a welcoming and inclusive environment for all contributors.
*   **Experimentation Embraced:** We recognize that true exploration involves venturing into uncharted territory, sometimes even challenging our own established guidelines. We embrace mistakes as learning opportunities, essential steps on the path to discovery. We're not afraid to break things to find better solutions, because the value of shared progress outweighs the fear of imperfection.

We believe that code, like any art form, is a collaborative endeavor. Former collaborators retain the full rights granted by the applicable licenses, including the freedom to refactor, enhance, and reimagine their work. This is not about ownership, but about fostering a continuous cycle of growth and innovation.

Join us in building a future where technology empowers, connects, and inspires.

## Community & Inclusivity

We are deeply committed to fostering a welcoming, supportive, and inclusive community for everyone who wants to contribute to this project.

*   **Neurodivergent Friendly:** We strive to create an environment that is understanding and accommodating of neurodivergent individuals. We recognize that different people have different needs and communication styles, and we aim to provide flexibility and support to ensure everyone can participate comfortably and effectively.
*   **LGBTQIA+ Friendly:** We are committed to being an inclusive space for members of the LGBTQIA+ community. We value diversity and aim to create an environment where everyone feels safe, respected, and empowered to be themselves.
*   **All Skill Levels Welcome:** Whether you're a complete beginner just starting your coding journey or a seasoned expert with years of experience, your contributions are valued here. We believe in learning together and supporting each other's growth. Don't hesitate to ask questions, suggest ideas, or tackle a small bug – every contribution helps!

We encourage open communication and mutual respect. If you have any concerns or suggestions on how we can improve our inclusivity, please reach out to the project maintainers or connect with us on Discord.

## Code of Conduct

Please note that this project is released with a [Contributor Covenant](https://www.contributor-covenant.org/version/2/0/code_of_conduct/) Code of Conduct. By participating in this project, you agree to abide by its terms.

## How to Contribute

There are many ways to contribute to this project, including:

*   **Reporting Bugs:** If you find a bug, please create a new issue on GitHub. Be sure to include as much information as possible, such as:
    *   The steps to reproduce the bug
    *   The expected behavior
    *   The actual behavior
    *   Your operating system and Python version
    *   Any relevant error messages or logs
*   **Suggesting Enhancements:** If you have an idea for a new feature or an improvement to an existing feature, please create a new issue on GitHub.
*   **Submitting Pull Requests:** If you're a developer and you'd like to contribute code, please follow these steps:
    1.  Fork the repository on GitHub.
    2.  Create a new branch for your changes.
    3.  Make your changes and commit them with clear, concise commit messages.
    4.  Submit a pull request to the `main` branch.

## Development Setup

1.  **Clone the Repository:**

    ```bash
    git clone https://github.com/Ktiseos-Nyx/Huggingface-Desktop/
    cd Huggingface-Desktop
    ```

2.  **Create a Virtual Environment:**

    It's highly recommended to use a virtual environment to isolate the project's dependencies.

    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**

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

4.  **Install Dependencies with UV or Pip:**

    *   **UV (Recommended):**

        ```bash
        uv pip install -r requirements.txt
        ```

    *   **Pip:**

        ```bash
        pip install -r requirements.txt
        ```

5.  **Install the Package in Editable Mode:**

        ```bash
        pip install -e .
        ```

## Coding Guidelines

*   **Embrace Experimentation:** Don't be afraid to try new things and break things! We value exploration and learning.
*   **Follow PEP 8:** Please follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code to maintain consistency.
*   **Use Clear and Concise Commit Messages:** Your commit messages should clearly describe the changes you've made.
*   **Write Unit Tests:** If you're adding new functionality, please write unit tests to ensure that it works correctly.
*   **Document Your Code:** Please document your code using docstrings.

## Pull Request Guidelines

*   **Create a Separate Branch:** Please create a separate branch for your changes.
*   **Keep Pull Requests Small:** Smaller pull requests are easier to review and merge.
*   **Include Tests:** If you're adding new functionality, please include unit tests.
*   **Update Documentation:** If you're making changes that affect the documentation, please update the documentation accordingly.
*   **Follow the Code of Conduct:** Please ensure that your pull request adheres to the Code of Conduct.

## Areas Where Help Is Needed

We're always looking for help with the following:

*   **Advanced Features:** Implementing more advanced features, such as incremental backups, version control integration, and support for large file storage (LFS).
*   **Cross-Platform Compatibility:** Ensuring that the tool works seamlessly on Windows, macOS, and Linux.
*   **User Interface Improvements:** Enhancing the user interface to make it even more intuitive and user-friendly.
*   **Testing and Bug Fixing:** Thoroughly testing the tool and fixing any bugs that are found.
*   **Documentation:** Improving the documentation to make it more comprehensive and easier to understand.

## Connect with Us

Join the discussion and get involved on our [Discord Server](https://discord.gg/HhBSvM9gBY)!

## Thank You!

Thank you for your interest in contributing to the Hugging Face Backup Tool! We appreciate your help in making this tool even better.
