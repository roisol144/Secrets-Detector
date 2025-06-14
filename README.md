# Secrets Detector

**Secrets Detector** is a tool designed to scan your codebase for sensitive information, such as API keys, passwords, and other secrets that may accidentally be exposed in your repositories.

## Prerequisites

To use this project, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Git](https://git-scm.com/)

---

## Installation and Setup

### 1. Clone the Repositories

First, clone this repository to your local machine:

```bash
git clone https://github.com/roisol144/Secrets-Detector.git
cd Secrets-Detector
```

Additionally, ensure you have the repository you'd like to scan for secrets cloned locally. For example, if you want to check a project stored on GitHub:

```bash
git clone https://github.com/example-user/example-repo.git
```
I used this one for testing my code:

```bash
git clone https://github.com/atrull/fake-public-secrets.git
```

You now have both repositories locally: `Secrets-Detector` and the target repository (e.g., `example-repo`).

---

### 2. Build the Docker Image

Before running the tool, you need to build the Docker image for **Secrets Detector**. Run the following command inside the `Secrets-Detector` directory:

```bash
docker build -t roisol144/secrets-detector .
```

This creates a Docker image named `roisol144/secrets-detector` that contains all the necessary dependencies to run the tool in an isolated environment.

---

## Usage

### Step 1: Navigate to the Target Repository

Use `cd` to change to the directory of the repository you'd like to scan. For example:

```bash
cd /path/to/example-repo
```

This step ensures the scanning process will run against the files in the target repository.

---

### Step 2: Run the Docker Container

Run the following command from inside the target repository:

```bash
docker run --rm -v $(pwd):/code roisol144/secrets-detector detect --no-git --report-path /code/output.json /code/.env
```

#### Explanation of the Command:
- `docker run`: Runs the Docker container.
- `--rm`: Automatically removes the container after it finishes executing.
- `-v $(pwd):/code`: Mounts the current directory (the target repository) to the `/code` directory inside the container. This allows the container to scan your repository files.
- `roisol144/secrets-detector`: The Docker image you built earlier.
- `detect`: The command to start scanning for secrets.
- `--no-git`: Skips scanning `.git` directories.
- `--report-path /code/output.json`: Saves the scan results to an `output.json` file in the current directory.
- `/code/.env`: Specifies the `.env` file to scan within the mounted `/code` directory.

#### Output:
- A file named `output.json` will be created in the current directory, containing the scan results.
- Log messages (including any leaks found or errors) will be printed to your console.

---

## Error Codes and Troubleshooting

The tool uses specific exit codes to indicate different outcomes or errors:

-   **Exit Code 0**: Successful execution, and no leaks were found.
-   **Exit Code 1**: General error. This can be due to various issues, such as:
    -   The Gitleaks tool itself failing during execution (not related to finding leaks).
    -   An unexpected Python exception occurred.
    -   Missing command-line arguments when running the script.
-   **Exit Code 2**: Gitleaks output file not found. This typically means the Gitleaks scan might have been successful (or not), but the expected JSON report file was not created or is missing.
-   **Exit Code 3**: Invalid Gitleaks output. The Gitleaks JSON report file was found, but its content could not be parsed (e.g., malformed JSON) or validated against the expected schema.
-   **Exit Code 4**: Gitleaks execution error. This indicates a problem reported by the Gitleaks tool itself through its own error codes (other than finding leaks).

Check the log output for detailed error messages that provide more context on the issue.

---

## Code Quality

This project uses **Black** for code formatting and **Flake8** for linting to maintain a consistent code style and identify potential issues.

### Running Linters Locally

You can run these checks locally to ensure your contributions meet the quality standards:

1.  **Install dependencies** (if you haven't already):
    ```bash
    pip install -r requirements.txt
    ```
    (Ensure `flake8` and `black` are listed in `requirements.txt`)

2.  **Run Black** to format files:
    ```bash
    black .
    ```

3.  **Run Flake8** to check for linting issues:
    ```bash
    flake8 .
    ```

### Docker Build Checks

These code quality checks (Black and Flake8) are also integrated into the Docker build process. If either Black (in check mode) or Flake8 reports issues, the Docker build will fail. This helps ensure that only quality code is included in the Docker image.

---

## Running the Test File

#### Why Use the Test File?
Using the provided test file helps verify that the tool is functioning correctly in your environment.

#### Test File:
In the Secrets-Detector directory there's a test file called "test_main.py".
Using mocks I set what i expect my program should return in certain cases.
You can run it using the following command:


```bash
pytest test_main.py
```