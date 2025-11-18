"""
DTOs for historico operations.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class HistoricoItemDTO:
    """DTO for historico item."""
    tabela: str
    id: str
    codsentenca: Optional[str] = None
    titulo: Optional[str] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None
    reccreatedby: Optional[str] = None
    prioridade: Optional[str] = None
    observacao: Optional[str] = None
    data_criacao: Optional[datetime] = None


@dataclass
class HistoricoResponseDTO:
    """DTO for historico response."""
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: list[HistoricoItemDTO]





