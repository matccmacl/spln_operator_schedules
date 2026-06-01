from abc import ABC, abstractmethod
import pandas as pd

class BaseScheduleProcessor(ABC):
    """
    Abstract Base Class for all Seaplane operator schedule processors.
    """
    @abstractmethod
    def process(self, file, filename) -> tuple[pd.DataFrame | None, str | None]:
        """
        Process the schedule file and return a tuple of (DataFrame, ErrorMessage).
        DataFrame must comply with the standardized schema:
        ['DATE TIME UTC', 'DATE TIME LOCAL', 'AIRLINE', 'FLT NUMBER', 'REG', 'FROM', 'TO', 'DIRECTION']
        """
        pass
