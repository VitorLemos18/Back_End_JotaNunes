"""
Use case for comparing registros.
"""
from typing import Optional
from ...domain.repositories.aud_repository import (
    IAudSQLRepository, IAudReportRepository, IAudFVRepository
)
from ...domain.repositories.dependencia_repository import IDependenciaRepository
from ..dto.comparacao_dto import RegistroComparacaoDTO, ComparacaoResponseDTO


class CompararRegistrosUseCase:
    """Use case to compare current and previous registro."""
    
    def __init__(
        self,
        aud_sql_repo: IAudSQLRepository,
        aud_report_repo: IAudReportRepository,
        aud_fv_repo: IAudFVRepository,
        dependencia_repo: IDependenciaRepository
    ):
        self._aud_sql_repo = aud_sql_repo
        self._aud_report_repo = aud_report_repo
        self._aud_fv_repo = aud_fv_repo
        self._dependencia_repo = dependencia_repo
    
    def execute(
        self, 
        tabela: str, 
        registro_id: str
    ) -> ComparacaoResponseDTO:
        """
        Execute the use case.
        
        Args:
            tabela: Table name (AUD_SQL, AUD_REPORT, AUD_FV)
            registro_id: Record identifier
            
        Returns:
            ComparacaoResponseDTO with current and previous records
        """
        tabela = tabela.upper()
        
        if tabela == 'AUD_SQL':
            return self._compare_sql(registro_id)
        elif tabela == 'AUD_REPORT':
            return self._compare_report(registro_id)
        elif tabela == 'AUD_FV':
            return self._compare_fv(int(registro_id))
        else:
            raise ValueError(f"Tabela inválida: {tabela}")
    
    def _compare_sql(self, codsentenca: str) -> ComparacaoResponseDTO:
        """Compare AUD_SQL records."""
        records = self._aud_sql_repo.get_all_by_id(codsentenca)
        
        if not records:
            raise ValueError("Registro não encontrado")
        
        # Current (most recent)
        current = records[0]
        observacao_atual = self._dependencia_repo.get_observacao_by_aud_sql(codsentenca)
        
        registro_atual = RegistroComparacaoDTO(
            id=current['codsentenca'],
            codsentenca=current['codsentenca'],
            titulo=current.get('titulo'),
            sentenca=current.get('sentenca'),
            aplicacao=current.get('aplicacao'),
            tamanho=current.get('tamanho'),
            reccreatedby=current.get('reccreatedby'),
            reccreatedon=current.get('reccreatedon'),
            observacao=observacao_atual
        )
        
        # Previous (if exists)
        registro_anterior: Optional[RegistroComparacaoDTO] = None
        if len(records) > 1:
            previous = records[1]
            observacao_anterior = self._dependencia_repo.get_observacao_by_aud_sql(
                codsentenca, 
                previous.get('reccreatedon')
            )
            
            registro_anterior = RegistroComparacaoDTO(
                id=previous['codsentenca'],
                codsentenca=previous['codsentenca'],
                titulo=previous.get('titulo'),
                sentenca=previous.get('sentenca'),
                aplicacao=previous.get('aplicacao'),
                tamanho=previous.get('tamanho'),
                reccreatedby=previous.get('reccreatedby'),
                reccreatedon=previous.get('reccreatedon'),
                observacao=observacao_anterior
            )
        
        return ComparacaoResponseDTO(
            tabela='AUD_SQL',
            registro_atual=registro_atual,
            registro_anterior=registro_anterior
        )
    
    def _compare_report(self, aud_id: str) -> ComparacaoResponseDTO:
        """Compare AUD_REPORT records."""
        records = self._aud_report_repo.get_all_by_id(aud_id)
        
        if not records:
            raise ValueError("Registro não encontrado")
        
        current = records[0]
        registro_atual = RegistroComparacaoDTO(
            id=current['id'],
            codigo=current.get('codigo'),
            descricao=current.get('descricao'),
            reccreatedby=current.get('reccreatedby'),
            reccreatedon=current.get('reccreatedon')
        )
        
        registro_anterior: Optional[RegistroComparacaoDTO] = None
        if len(records) > 1:
            previous = records[1]
            registro_anterior = RegistroComparacaoDTO(
                id=previous['id'],
                codigo=previous.get('codigo'),
                descricao=previous.get('descricao'),
                reccreatedby=previous.get('reccreatedby'),
                reccreatedon=previous.get('reccreatedon')
            )
        
        return ComparacaoResponseDTO(
            tabela='AUD_REPORT',
            registro_atual=registro_atual,
            registro_anterior=registro_anterior
        )
    
    def _compare_fv(self, aud_id: int) -> ComparacaoResponseDTO:
        """Compare AUD_FV records."""
        records = self._aud_fv_repo.get_all_by_id(aud_id)
        
        if not records:
            raise ValueError("Registro não encontrado")
        
        current = records[0]
        registro_atual = RegistroComparacaoDTO(
            id=str(current['id']),
            nome=current.get('nome'),
            descricao=current.get('descricao'),
            idcategoria=current.get('idcategoria'),
            ativo=current.get('ativo'),
            reccreatedby=current.get('reccreatedby'),
            reccreatedon=current.get('reccreatedon')
        )
        
        registro_anterior: Optional[RegistroComparacaoDTO] = None
        if len(records) > 1:
            previous = records[1]
            registro_anterior = RegistroComparacaoDTO(
                id=str(previous['id']),
                nome=previous.get('nome'),
                descricao=previous.get('descricao'),
                idcategoria=previous.get('idcategoria'),
                ativo=previous.get('ativo'),
                reccreatedby=previous.get('reccreatedby'),
                reccreatedon=previous.get('reccreatedon')
            )
        
        return ComparacaoResponseDTO(
            tabela='AUD_FV',
            registro_atual=registro_atual,
            registro_anterior=registro_anterior
        )





