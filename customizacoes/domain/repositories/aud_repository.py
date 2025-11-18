"""
Domain repository interfaces for AUD tables.
Following Dependency Inversion Principle (SOLID).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class IAudSQLRepository(ABC):
    """Interface for AUD_SQL repository operations."""
    
    @abstractmethod
    def get_by_id(self, codsentenca: str) -> Optional[Dict[str, Any]]:
        """Get the most recent record by CODSENTENCA."""
        pass
    
    @abstractmethod
    def get_all_by_id(self, codsentenca: str) -> List[Dict[str, Any]]:
        """Get all records with the same CODSENTENCA, ordered by date DESC."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all records."""
        pass


class IAudReportRepository(ABC):
    """Interface for AUD_REPORT repository operations."""
    
    @abstractmethod
    def get_by_id(self, aud_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent record by ID."""
        pass
    
    @abstractmethod
    def get_all_by_id(self, aud_id: str) -> List[Dict[str, Any]]:
        """Get all records with the same ID, ordered by date DESC."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all records."""
        pass


class IAudFVRepository(ABC):
    """Interface for AUD_FV repository operations."""
    
    @abstractmethod
    def get_by_id(self, aud_id: int) -> Optional[Dict[str, Any]]:
        """Get the most recent record by ID."""
        pass
    
    @abstractmethod
    def get_all_by_id(self, aud_id: int) -> List[Dict[str, Any]]:
        """Get all records with the same ID, ordered by date DESC."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all records."""
        pass





