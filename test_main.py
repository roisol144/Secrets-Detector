import os
import json
import pytest
from main import execute_gitleaks, parse_and_format_gitleaks_output
from exceptions import GitleaksFileNotFound


# Test if running gitleaks command works
def test_execute_gitleaks_success(mocker):
    # Mock subprocess.run in the context of the main module
    mock_subprocess = mocker.patch("subprocess.run")
    mock_subprocess.return_value.returncode = 0

    # Execute the function
    execute_gitleaks(["detect", "--no-git", "--report-path", "output.json", "."])

    # Assert the subprocess was called once
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
            "Description": "Mock leak description"  # Update key to match the function's logic
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
                "description": "Mock leak description"
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
        {} 
    ]
    with open(output_file, "w") as f:
        json.dump(output_data, f)

    expected = {
        "findings": [
            {"filename": "example.txt", "line_range": "10 - 0", "description": "No description available"},
            {"filename": "N/A", "line_range": "5 - 7", "description": "No description available"},
            {"filename": "N/A", "line_range": "0 - 0", "description": "No description available"}
        ]
    }

    result = parse_and_format_gitleaks_output(str(output_file))
    assert result == expected


