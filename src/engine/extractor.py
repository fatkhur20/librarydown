from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseExtractor(ABC):
    """
    Abstract base class for a data extractor.
    It expects to be initialized with the core JSON data structure.
    """

    def __init__(self, json_data: Dict[str, Any]):
        self.json_data = json_data

    @abstractmethod
    def extract_all_data(self) -> Dict[str, Any]:
        """
        Extracts all the required metadata from the JSON data and returns it
        in a structured format.
        """
        raise NotImplementedError
