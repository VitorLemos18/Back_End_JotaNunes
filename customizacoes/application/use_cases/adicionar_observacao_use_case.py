"""
Use case for adding observation to registro.
"""
from ...domain.repositories.observacao_repository import IObservacaoRepository
from ...domain.repositories.dependencia_repository import IDependenciaRepository


class AdicionarObservacaoUseCase:
    """Use case to add observation to a registro."""
    
    def __init__(
        self,
        observacao_repo: IObservacaoRepository,
        dependencia_repo: IDependenciaRepository
    ):
        self._observacao_repo = observacao_repo
        self._dependencia_repo = dependencia_repo
    
    def execute(
        self,
        tabela: str,
        registro_id: str,
        texto: str,
        user_id: int
    ) -> dict:
        """
        Execute the use case.
        
        Args:
            tabela: Table name (AUD_SQL, AUD_REPORT, AUD_FV)
            registro_id: Record identifier
            texto: Observation text
            user_id: User ID who created the observation
            
        Returns:
            dict with success status and created IDs
        """
        # Create observation
        observacao = self._observacao_repo.create(texto, user_id)
        
        # Associate with dependencia
        result = self._dependencia_repo.create_with_observacao(
            tabela=tabela,
            registro_id=registro_id,
            texto_observacao=texto,
            user_id=user_id
        )
        
        return {
            "success": True,
            "message": result.get("message", "Observação adicionada com sucesso"),
            "observacao_id": observacao['id'],
            "dependencia_id": result.get("dependencia_id")
        }





