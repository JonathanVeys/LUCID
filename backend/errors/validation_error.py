from typing import Optional, Literal
from enum import Enum
from dataclasses import dataclass


ErrorType = Literal["SQL Syntax", "JSON Syntax", "VisSpec Schema", "Chart Error", "SQL Semantic", "SQL Execution"]

@dataclass
class ValidationError():
    type:ErrorType
    details:str
    location:Optional[str]=None

    def __str__(self):
        return f"{self.type} Error: {self.details}"


if __name__ == "__main__":
    test_error = ValidationError(
        type="SQL Syntax",
        details="SQL failed to run",
        location="injection"
    )
    print(test_error)