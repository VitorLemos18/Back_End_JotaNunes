"""
DTOs for comparison operations.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class RegistroComparacaoDTO:
    """DTO for registro comparison."""
    id: str
    codsentenca: Optional[str] = None
    titulo: Optional[str] = None
    sentenca: Optional[str] = None
    aplicacao: Optional[str] = None
    tamanho: Optional[int] = None
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    nome: Optional[str] = None
    idcategoria: Optional[int] = None
    ativo: Optional[bool] = None
    reccreatedby: Optional[str] = None
    reccreatedon: Optional[datetime] = None
    observacao: Optional[str] = None


@dataclass
class ComparacaoResponseDTO:
    """DTO for comparison response."""
    tabela: str
    registro_atual: RegistroComparacaoDTO
    registro_anterior: Optional[RegistroComparacaoDTO] = None





