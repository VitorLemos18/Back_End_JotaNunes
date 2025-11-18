"""
Infrastructure implementation of IObservacaoRepository using Django ORM.
"""
from typing import Optional, Dict, Any
from ...domain.repositories.observacao_repository import IObservacaoRepository
from ...infrastructure.persistence.models import Observacao


class DjangoObservacaoRepository(IObservacaoRepository):
    """Django implementation of Observacao repository."""
    
    def create(self, texto: str, user_id: int) -> Dict[str, Any]:
        """Create a new observation."""
        observacao = Observacao.objects.create(
            texto=texto,
            criado_por_id=user_id
        )
        
        return {
            'id': observacao.id,
            'texto': observacao.texto,
            'data': observacao.data,
            'criado_por_id': observacao.criado_por_id
        }
    
    def get_by_id(self, observacao_id: int) -> Optional[Dict[str, Any]]:
        """Get observation by ID."""
        try:
            observacao = Observacao.objects.get(id=observacao_id)
            return {
                'id': observacao.id,
                'texto': observacao.texto,
                'data': observacao.data,
                'criado_por_id': observacao.criado_por_id
            }
        except Observacao.DoesNotExist:
            return None





