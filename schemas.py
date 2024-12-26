from pydantic import BaseModel, RootModel
from typing import Optional

class Leak(BaseModel):
    File: Optional[str] = "N/A"
    StartLine: Optional[int] = 0
    EndLine: Optional[int] = 0
    Description: Optional[str] = "No description available" 


class GitleaksOutput(RootModel[list[Leak]]): # RootModel is based on the structure of output.json of gitleaks
    pass