import subprocess
import sys
import json
import logging
from exceptions import (
    GitleaksFileNotFound,
    InvalidGitleaksOutput,
    GitleaksExecutionError,
)
from schemas import GitleaksOutput


def execute_gitleaks(args: list[str], logger: logging.Logger) -> None:
    # Building the Gitleaks command
    gitleaks_command = (
        ["gitleaks"] + args + ["--report-path", "/code/output.json"]
    )

    # Use subprocess to run shell command
    result = subprocess.run(gitleaks_command, capture_output=True, text=True)

    # Handle cases based on the return code
    if result.returncode == 0:
        logger.info("No leaks were found. Your code is clean !")
    elif result.returncode == 1:
        logger.info(
            "Gitleaks found leaks in your code. "
            "Check output file for detailes."
        )
    else:
        # The error is logged in main's except block
        raise Exception(
            f"Gitleaks failed with the following error: {result.stderr}"
        )


def parse_and_format_gitleaks_output(output: str) -> dict:
    try:
        with open(output, "r") as f:
            data = json.load(f)

        # Use Pydantic to validate the data
        validated_data = GitleaksOutput.model_validate(data).root

        # Format the output file
        findings = []  # of format List[Dict[key:str, value: str]]
        for leak in validated_data:
            findings.append(
                {
                    "filename": getattr(leak, "File", "N/A"),
                    "line_range": (
                        f"{getattr(leak, 'StartLine', 0)} - "
                        f"{getattr(leak, 'EndLine', 0)}"
                    ),
                    "description": getattr(
                        leak, "Description", "No description available"
                    ),
                }
            )

        return {"findings": findings}

    except FileNotFoundError:
        raise GitleaksFileNotFound("Gitleaks file is missing.")
    except json.JSONDecodeError:
        raise InvalidGitleaksOutput(
            "Invalid Gitleaks JSON format - unable to parse file."
        )
    except ValueError:
        raise InvalidGitleaksOutput(
            "Invalid Gitleaks data structure - unexpected values found."
        )


# Error handler function
def error_handler(exit_code, error_message, logger: logging.Logger):
    error_output = {"exit_code": exit_code, "error_message": error_message}

    logger.error(json.dumps(error_output, indent=4))
    sys.exit(exit_code)


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Add a StreamHandler if no handlers are configured, for standalone execution
    if not logger.handlers and not logging.getLogger().handlers: # Check root logger too
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # Prevent propagation to root if we add a handler, to avoid duplicate logs if root also gets configured
        # logger.propagate = False # Only if we are sure this is the desired behavior

    args = sys.argv[1:]
    if not args:
        logger.warning("Follow this format: python main.py <gitleaks command>") # Changed to warning
        sys.exit(1)

    try:
        execute_gitleaks(args, logger)
        parsed_gitleaks_dict = parse_and_format_gitleaks_output("/code/output.json")
        logger.info(json.dumps(parsed_gitleaks_dict, indent=4)) # This line should be active

    except GitleaksFileNotFound as e:
        logger.error(f"Error type: {type(e).__name__}, Message: {str(e)}")
        error_handler(2, f"GitleaksFileNotFound: {str(e)}", logger)
    except InvalidGitleaksOutput as e:
        logger.error(f"Error type: {type(e).__name__}, Message: {str(e)}")
        error_handler(3, f"InvalidGitleaksOutput: {str(e)}", logger)
    except GitleaksExecutionError as e:
        logger.error(f"Error type: {type(e).__name__}, Message: {str(e)}")
        error_handler(4, f"GitleaksExecutionError: {str(e)}", logger)
    except Exception as e:
        logger.error(f"Error type: {type(e).__name__}, Message: {str(e)}")
        error_handler(1, f"An unexpected error occurred: {str(e)}", logger)


if __name__ == "__main__":
    main()
