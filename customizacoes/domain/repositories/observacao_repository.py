"""
Domain repository interface for Observacoes.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class IObservacaoRepository(ABC):
    """Interface for Observacao repository operations."""
    
    @abstractmethod
    def create(self, texto: str, user_id: int) -> Dict[str, Any]:
        """Create a new observation."""
        pass
    
    @abstractmethod
    def get_by_id(self, observacao_id: int) -> Optional[Dict[str, Any]]:
        """Get observation by ID."""
        pass





