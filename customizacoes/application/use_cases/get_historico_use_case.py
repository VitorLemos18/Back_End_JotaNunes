"""
Use case for getting historico de alterações.
"""
from typing import List, Optional
from datetime import datetime
from ...domain.repositories.aud_repository import (
    IAudSQLRepository, IAudReportRepository, IAudFVRepository
)
from ...domain.repositories.dependencia_repository import IDependenciaRepository
from ..dto.historico_dto import HistoricoItemDTO, HistoricoResponseDTO


class GetHistoricoUseCase:
    """Use case to get historico de alterações."""
    
    def __init__(
        self,
        aud_sql_repo: IAudSQLRepository,
        aud_report_repo: Optional[IAudReportRepository],
        aud_fv_repo: Optional[IAudFVRepository],
        dependencia_repo: IDependenciaRepository
    ):
        self._aud_sql_repo = aud_sql_repo
        self._aud_report_repo = aud_report_repo
        self._aud_fv_repo = aud_fv_repo
        self._dependencia_repo = dependencia_repo
    
    def execute(
        self, 
        page: int = 1, 
        page_size: int = 20
    ) -> HistoricoResponseDTO:
        """
        Execute the use case.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            HistoricoResponseDTO with paginated results
        """
        historico: List[HistoricoItemDTO] = []
        
        # Get AUD_SQL records
        sql_records = self._aud_sql_repo.get_all()
        for reg in sql_records:
            prioridade = self._dependencia_repo.get_prioridade_by_aud_sql(reg['codsentenca'])
            observacao = self._dependencia_repo.get_observacao_by_aud_sql(reg['codsentenca'])
            
            historico.append(HistoricoItemDTO(
                tabela='AUD_SQL',
                id=reg['codsentenca'],
                codsentenca=reg['codsentenca'],
                reccreatedby=reg.get('reccreatedby'),
                titulo=reg.get('titulo'),
                prioridade=prioridade,
                observacao=observacao,
                data_criacao=reg.get('reccreatedon')
            ))
        
        # Get AUD_REPORT records
        if self._aud_report_repo:
            report_records = self._aud_report_repo.get_all()
            for reg in report_records:
                prioridade = self._dependencia_repo.get_prioridade_by_aud_report(reg['id'])
                observacao = self._dependencia_repo.get_observacao_by_aud_report(reg['id'])
                
                historico.append(HistoricoItemDTO(
                    tabela='AUD_REPORT',
                    id=reg['id'],
                    reccreatedby=reg.get('reccreatedby'),
                    descricao=reg.get('descricao'),
                    prioridade=prioridade,
                    observacao=observacao,
                    data_criacao=reg.get('reccreatedon')
                ))
        
        # Get AUD_FV records
        if self._aud_fv_repo:
            fv_records = self._aud_fv_repo.get_all()
            for reg in fv_records:
                prioridade = self._dependencia_repo.get_prioridade_by_aud_fv(reg['id'])
                observacao = self._dependencia_repo.get_observacao_by_aud_fv(reg['id'])
                
                historico.append(HistoricoItemDTO(
                    tabela='AUD_FV',
                    id=str(reg['id']),
                    reccreatedby=reg.get('reccreatedby'),
                    nome=reg.get('nome'),
                    prioridade=prioridade,
                    observacao=observacao,
                    data_criacao=reg.get('reccreatedon')
                ))
        
        # Sort by date
        historico.sort(key=lambda x: x.data_criacao or datetime.min, reverse=True)
        
        # Pagination
        total = len(historico)
        start = (page - 1) * page_size
        end = start + page_size
        results = historico[start:end]
        
        return HistoricoResponseDTO(
            count=total,
            next=f'?page={page + 1}&page_size={page_size}' if end < total else None,
            previous=f'?page={page - 1}&page_size={page_size}' if page > 1 else None,
            results=results
        )
