import json
import sys
import pytest
import logging
from unittest.mock import patch, MagicMock
from main import main, execute_gitleaks, parse_and_format_gitleaks_output
from exceptions import (
    GitleaksFileNotFound,
    InvalidGitleaksOutput,
    GitleaksExecutionError,
)


# Test if running gitleaks command works
def test_execute_gitleaks_success(mocker):
    # Mock subprocess.run in the context of the main module
    mock_subprocess = mocker.patch("subprocess.run")
    mock_subprocess.return_value.returncode = 0
    mock_logger = MagicMock()

    # Execute the function
    execute_gitleaks(
        ["detect", "--no-git", "--report-path", "output.json", "."], mock_logger
    )

    # Assert the subprocess was called once
    mock_logger.info.assert_any_call("No leaks were found. Your code is clean !")
    mock_subprocess.assert_called_once()


# Test if Gitleaks output file is missing
def test_parse_missing_output():
    with pytest.raises(GitleaksFileNotFound):
        # Call the function with a non-existent file
        parse_and_format_gitleaks_output("nonexistent.json")


# Test for valid output
def test_parse_and_format_output(tmp_path):
    # Creating a mock
    output_file = tmp_path / "output.json"
    output_data = [
        {
            "File": "example.txt",
            "StartLine": 10,
            "EndLine": 12,
            # Update key to match the function's logic
            "Description": "Mock leak description",
        }
    ]
    # Write mock output data to the temporary file
    with open(output_file, "w") as f:
        json.dump(output_data, f)

    # Set the expected result
    expected_output = {
        "findings": [
            {
                "filename": "example.txt",
                "line_range": "10 - 12",
                "description": "Mock leak description",
            }
        ]
    }

    # Execute function and assert the result
    result = parse_and_format_gitleaks_output(str(output_file))
    assert result == expected_output


# Testing case where some fields are missing
def test_parse_with_missing_fields(tmp_path):
    output_file = tmp_path / "output.json"
    output_data = [
        {"File": "example.txt", "StartLine": 10},  # No EndLine and
        {"StartLine": 5, "EndLine": 7},  # No File and description
        {},
    ]
    with open(output_file, "w") as f:
        json.dump(output_data, f)

    expected = {
        "findings": [
            {
                "filename": "example.txt",
                "line_range": "10 - 0",
                "description": "No description available",
            },
            {
                "filename": "N/A",
                "line_range": "5 - 7",
                "description": "No description available",
            },
            {
                "filename": "N/A",
                "line_range": "0 - 0",
                "description": "No description available",
            },
        ]
    }

    result = parse_and_format_gitleaks_output(str(output_file))
    assert result == expected


# Tests for main() function
def test_main_no_leaks_found(mocker, caplog):
    """Test main() when gitleaks finds no leaks."""
    mocker.patch("sys.argv", ["main.py", "detect"])
    mock_execute = mocker.patch("main.execute_gitleaks")
    mock_parse = mocker.patch(
        "main.parse_and_format_gitleaks_output",
        return_value={"findings": []},
    )

    caplog.set_level(logging.INFO) # Capture all INFO logs
    main()

    # Check that execute_gitleaks was called (logger arg is now from main)
    # We don't need to check the logger instance itself if we trust getLogger works
    mock_execute.assert_called_once()
    # Get the logger instance that was passed to mock_execute
    passed_logger_to_execute = mock_execute.call_args[0][1]

    mock_parse.assert_called_once_with("/code/output.json")

    expected_log_json = json.dumps({"findings": []}, indent=4)
    found_json_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "INFO" and record.message == expected_log_json:
            found_json_log = True
            break
    assert found_json_log, f"Expected JSON log not found. Records: {caplog.records}"

    # Check for the "No leaks found" message from execute_gitleaks
    # This requires execute_gitleaks to actually log, so we can't fully mock it if we want to test its logs.
    # For now, we assume execute_gitleaks is tested separately or we trust its logging.
    # If execute_gitleaks was not mocked, its "No leaks" log would also be in caplog.records.
    # Since execute_gitleaks is mocked, we check the logger it was called with.
    # This test is primarily for main's direct logging.

def test_main_leaks_found(mocker, caplog):
    """Test main() when gitleaks finds leaks."""
    mocker.patch("sys.argv", ["main.py", "detect", "--verbose"])
    mock_execute = mocker.patch("main.execute_gitleaks")
    mock_findings_data = [
        {"description": "leak1", "file": "file1.py", "line": 10}
    ]
    mock_parse = mocker.patch(
        "main.parse_and_format_gitleaks_output",
        return_value={"findings": mock_findings_data},
    )

    caplog.set_level(logging.INFO) # Capture all INFO logs
    main()

    mock_execute.assert_called_once()
    mock_parse.assert_called_once_with("/code/output.json")

    expected_log_json = json.dumps({"findings": mock_findings_data}, indent=4)
    found_json_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "INFO" and record.message == expected_log_json:
            found_json_log = True
            break
    assert found_json_log, f"Expected JSON log not found. Records: {caplog.records}"


def test_main_gitleaks_command_fails(mocker, caplog):
    """Test main() when the gitleaks command itself fails."""
    mocker.patch("sys.argv", ["main.py", "detect"])
    mocker.patch(
        "main.execute_gitleaks",
        side_effect=Exception("Gitleaks tool execution failed"),
    )

    with pytest.raises(SystemExit) as e, caplog.at_level(logging.ERROR):
        main()

    assert e.value.code == 1
    expected_log_message = json.dumps(
        {
            "exit_code": 1,
            "error_message": "An unexpected error occurred: Gitleaks tool execution failed",
        },
        indent=4,
    )
    # Check for the specific error log from main's except block
    found_main_error_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "ERROR" and \
           "Error type: Exception, Message: Gitleaks tool execution failed" in record.message:
            found_main_error_log = True
            break
    assert found_main_error_log, "Main specific error log not found"

    # Check for the error_handler's JSON log
    assert expected_log_message in caplog.text


def test_main_gitleaks_file_not_found(mocker, caplog):
    """Test main() when gitleaks output file is not found."""
    mocker.patch("sys.argv", ["main.py", "detect"])
    mocker.patch("main.execute_gitleaks")  # Simulate successful execution
    mocker.patch(
        "main.parse_and_format_gitleaks_output",
        side_effect=GitleaksFileNotFound("Report file missing"),
    )

    with pytest.raises(SystemExit) as e, caplog.at_level(logging.ERROR):
        main()

    assert e.value.code == 2
    expected_log_message = json.dumps(
        {
            "exit_code": 2,
            "error_message": "GitleaksFileNotFound: Gitleaks output file is missing. Report file missing",
        },
        indent=4,
    )
    # Check for the specific error log from main's except block
    found_main_error_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "ERROR" and \
           "Error type: GitleaksFileNotFound, Message: Gitleaks output file is missing. Report file missing" in record.message:
            found_main_error_log = True
            break
    assert found_main_error_log, "Main specific error log for GitleaksFileNotFound not found"

    assert expected_log_message in caplog.text


def test_main_invalid_gitleaks_output(mocker, caplog):
    """Test main() when gitleaks output is invalid."""
    mocker.patch("sys.argv", ["main.py", "detect"])
    mocker.patch("main.execute_gitleaks")  # Simulate successful execution
    mocker.patch(
        "main.parse_and_format_gitleaks_output",
        side_effect=InvalidGitleaksOutput("Cannot parse JSON"),
    )

    with pytest.raises(SystemExit) as e, caplog.at_level(logging.ERROR):
        main()

    assert e.value.code == 3
    expected_log_message = json.dumps(
        {
            "exit_code": 3,
            "error_message": "InvalidGitleaksOutput: The output from Gitleaks could not be parsed.Cannot parse JSON",
        },
        indent=4,
    )
    # Check for the specific error log from main's except block
    found_main_error_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "ERROR" and \
           "Error type: InvalidGitleaksOutput, Message: The output from Gitleaks could not be parsed.Cannot parse JSON" in record.message:
            found_main_error_log = True
            break
    assert found_main_error_log, "Main specific error log for InvalidGitleaksOutput not found"

    assert expected_log_message in caplog.text


def test_main_gitleaks_execution_error(mocker, caplog):
    """Test main() for GitleaksExecutionError."""
    mocker.patch("sys.argv", ["main.py", "detect"])
    # This error would typically be raised by execute_gitleaks if gitleaks itself had an internal error
    # For this test, we'll have execute_gitleaks raise it directly to test the handler
    mocker.patch(
        "main.execute_gitleaks",
        side_effect=GitleaksExecutionError("Gitleaks internal error"),
    )

    with pytest.raises(SystemExit) as e, caplog.at_level(logging.ERROR):
        main()

    assert e.value.code == 4
    expected_log_message = json.dumps(
        {
            "exit_code": 4,
            "error_message": "GitleaksExecutionError: Gitleaks failed during execution: Gitleaks internal error",
        },
        indent=4,
    )
    # Check for the specific error log from main's except block
    found_main_error_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "ERROR" and \
           "Error type: GitleaksExecutionError, Message: Gitleaks failed during execution: Gitleaks internal error" in record.message:
            found_main_error_log = True
            break
    assert found_main_error_log, "Main specific error log for GitleaksExecutionError not found"

    assert expected_log_message in caplog.text

def test_main_no_args(mocker, caplog):
    """Test main() when no arguments are provided."""
    mocker.patch("sys.argv", ["main.py"])
    caplog.set_level(logging.WARNING) # As the log is now a warning

    with pytest.raises(SystemExit) as e:
        main()

    assert e.value.code == 1
    found_log = False
    for record in caplog.records:
        if record.name == "main" and record.levelname == "WARNING" and \
           "Follow this format: python main.py <gitleaks command>" in record.message:
            found_log = True
            break
    assert found_log, f"Warning for no args not found. Records: {caplog.records}"
