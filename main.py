import subprocess
import sys
import json
from exceptions import GitleaksFileNotFound, InvalidGitleaksOutput, GitleaksExecutionError
from schemas import GitleaksOutput

def execute_gitleaks(args: list[str]) -> None:
    # Building the Gitleaks command
    gitleaks_command = ["gitleaks"] + args + ["--report-path", "/code/output.json"]
    
    # Use subprocess to run shell command
    result = subprocess.run(gitleaks_command, capture_output=True, text=True)
    
    # Handle cases based on the return code
    if result.returncode == 0:
        print("No leaks were found. Your code is clean !")
    elif result.returncode == 1:
        print("Gitleaks found leaks in your code. Check output file for detailes.")
    else:
        raise Exception(f"Gitleaks failed with the following error: {result.stderr}")
        
        

def parse_and_format_gitleaks_output(output: str) -> dict:
    try:
        with open(output, "r") as f:
            data = json.load(f)
        
        # Use Pydantic to validate the data
        validated_data = GitleaksOutput.model_validate(data).root
        
        # Format the output file
        findings = []  # of format List[Dict[key:str, value: str]]
        for leak in validated_data:
            findings.append({
                "filename": getattr(leak, "File", "N/A"),
                "line_range": f"{getattr(leak, 'StartLine', 0)} - {getattr(leak, 'EndLine', 0)}",
                "description": getattr(leak, "Description", "No description available")
            })
            
        return {"findings": findings}
         
    except FileNotFoundError:
        raise GitleaksFileNotFound("Gitleaks file is missing.")
    except json.JSONDecodeError:
        raise InvalidGitleaksOutput("Invalid Gitleaks JSON format - unable to parse file.")
    except ValueError:
        raise InvalidGitleaksOutput("Invalid Gitleaks data structure - unexpected values found.")
    
# Error handler function
def error_handler(exit_code, error_message):
    error_output = {
        "exit_code": exit_code,
        "error_message": error_message
        }
    
    print(json.dumps(error_output, indent=4))
    sys.exit(exit_code)
    
def main():
    # parsing arguments that were passed to the script
    args = sys.argv[1:]
    if not args:
        print("Follow this format: python main.py <gitleaks command>")
        sys.exit(1)
    
    try:
        execute_gitleaks(args)
        parsed_gitleaks_dict = parse_and_format_gitleaks_output("/code/output.json")
        print(json.dumps(parsed_gitleaks_dict, indent=4))
        
    except GitleaksFileNotFound:
        error_handler(1, "Gitleaks output is missing.")
    except InvalidGitleaksOutput:
        error_handler(1, "Invalid Gitleaks output")
    except GitleaksExecutionError:
        error_handler(1, "Fail during execution.")
    except Exception as e:
        error_handler(1, str(e))

if __name__ == "__main__":
    main()
    
