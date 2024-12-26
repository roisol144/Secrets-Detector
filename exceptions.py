class GitleaksFileNotFound(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Gitleaks output file is missing. {message}")
        
class InvalidGitleaksOutput(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"The output from Gitleaks could not be parsed.{message}")

class GitleaksExecutionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(f"Gitleaks failed during execution: {message}")
