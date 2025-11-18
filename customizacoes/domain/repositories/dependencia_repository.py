"""
Domain repository interface for Dependencias.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class IDependenciaRepository(ABC):
    """Interface for Dependencias repository operations."""
    
    @abstractmethod
    def get_by_aud_sql(self, codsentenca: str) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_SQL CODSENTENCA."""
        pass
    
    @abstractmethod
    def get_by_aud_report(self, aud_id: str) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_REPORT ID."""
        pass
    
    @abstractmethod
    def get_by_aud_fv(self, aud_id: int) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_FV ID."""
        pass
    
    @abstractmethod
    def get_observacao_by_aud_sql(self, codsentenca: str, data_limite: Optional[datetime] = None) -> Optional[str]:
        """Get observation text for AUD_SQL record."""
        pass
    
    @abstractmethod
    def get_prioridade_by_aud_sql(self, codsentenca: str) -> Optional[str]:
        """Get priority level for AUD_SQL record."""
        pass
    
    @abstractmethod
    def get_prioridade_by_aud_report(self, aud_id: str) -> Optional[str]:
        """Get priority level for AUD_REPORT record."""
        pass
    
    @abstractmethod
    def get_prioridade_by_aud_fv(self, aud_id: int) -> Optional[str]:
        """Get priority level for AUD_FV record."""
        pass
    
    @abstractmethod
    def get_observacao_by_aud_report(self, aud_id: str, data_limite: Optional[datetime] = None) -> Optional[str]:
        """Get observation text for AUD_REPORT record."""
        pass
    
    @abstractmethod
    def get_observacao_by_aud_fv(self, aud_id: int, data_limite: Optional[datetime] = None) -> Optional[str]:
        """Get observation text for AUD_FV record."""
        pass
    
    @abstractmethod
    def create_with_observacao(
        self, 
        tabela: str, 
        registro_id: str, 
        texto_observacao: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Create or update dependencia with observation."""
        pass

