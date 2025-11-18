"""
Infrastructure implementation of IDependenciaRepository using Django ORM.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from ...domain.repositories.dependencia_repository import IDependenciaRepository
from ...infrastructure.persistence.models import (
    CadastroDependencias, CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV
)


class DjangoDependenciaRepository(IDependenciaRepository):
    """Django implementation of Dependencia repository."""
    
    def get_by_aud_sql(self, codsentenca: str) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_SQL CODSENTENCA."""
        deps = CadastroDependencias.objects.filter(
            id_aud_sql=codsentenca
        ).select_related('id_prioridade', 'id_observacao')
        
        return [self._to_dict(dep) for dep in deps]
    
    def get_by_aud_report(self, aud_id: str) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_REPORT ID."""
        deps = CadastroDependencias.objects.filter(
            id_aud_report=aud_id
        ).select_related('id_prioridade', 'id_observacao')
        
        return [self._to_dict(dep) for dep in deps]
    
    def get_by_aud_fv(self, aud_id: int) -> List[Dict[str, Any]]:
        """Get all dependencias by AUD_FV ID."""
        deps = CadastroDependencias.objects.filter(
            id_aud_fv=aud_id
        ).select_related('id_prioridade', 'id_observacao')
        
        return [self._to_dict(dep) for dep in deps]
    
    def get_observacao_by_aud_sql(
        self, 
        codsentenca: str, 
        data_limite: Optional[datetime] = None
    ) -> Optional[str]:
        """Get observation text for AUD_SQL record."""
        deps = CadastroDependencias.objects.filter(
            id_aud_sql=codsentenca,
            id_observacao__isnull=False
        ).select_related('id_observacao').order_by('-id_observacao__data')
        
        if data_limite:
            deps = deps.filter(id_observacao__data__lte=data_limite)
        
        dep = deps.first()
        return dep.id_observacao.texto if dep and dep.id_observacao else None
    
    def get_prioridade_by_aud_sql(self, codsentenca: str) -> Optional[str]:
        """Get priority level for AUD_SQL record."""
        dep = CadastroDependencias.objects.filter(
            id_aud_sql=codsentenca,
            id_prioridade__isnull=False
        ).select_related('id_prioridade').first()
        
        return dep.id_prioridade.nivel if dep and dep.id_prioridade else None
    
    def get_prioridade_by_aud_report(self, aud_id: str) -> Optional[str]:
        """Get priority level for AUD_REPORT record."""
        dep = CadastroDependencias.objects.filter(
            id_aud_report=aud_id,
            id_prioridade__isnull=False
        ).select_related('id_prioridade').first()
        
        return dep.id_prioridade.nivel if dep and dep.id_prioridade else None
    
    def get_prioridade_by_aud_fv(self, aud_id: int) -> Optional[str]:
        """Get priority level for AUD_FV record."""
        dep = CadastroDependencias.objects.filter(
            id_aud_fv=aud_id,
            id_prioridade__isnull=False
        ).select_related('id_prioridade').first()
        
        return dep.id_prioridade.nivel if dep and dep.id_prioridade else None
    
    def get_observacao_by_aud_report(
        self, 
        aud_id: str, 
        data_limite: Optional[datetime] = None
    ) -> Optional[str]:
        """Get observation text for AUD_REPORT record."""
        deps = CadastroDependencias.objects.filter(
            id_aud_report=aud_id,
            id_observacao__isnull=False
        ).select_related('id_observacao').order_by('-id_observacao__data')
        
        if data_limite:
            deps = deps.filter(id_observacao__data__lte=data_limite)
        
        dep = deps.first()
        return dep.id_observacao.texto if dep and dep.id_observacao else None
    
    def get_observacao_by_aud_fv(
        self, 
        aud_id: int, 
        data_limite: Optional[datetime] = None
    ) -> Optional[str]:
        """Get observation text for AUD_FV record."""
        deps = CadastroDependencias.objects.filter(
            id_aud_fv=aud_id,
            id_observacao__isnull=False
        ).select_related('id_observacao').order_by('-id_observacao__data')
        
        if data_limite:
            deps = deps.filter(id_observacao__data__lte=data_limite)
        
        dep = deps.first()
        return dep.id_observacao.texto if dep and dep.id_observacao else None
    
    def create_with_observacao(
        self, 
        tabela: str, 
        registro_id: str, 
        texto_observacao: str, 
        user_id: int
    ) -> Dict[str, Any]:
        """Create or update dependencia with observation."""
        from ...infrastructure.persistence.models import Observacao
        
        # Create observation
        observacao = Observacao.objects.create(
            texto=texto_observacao,
            criado_por_id=user_id
        )
        
        # Find existing dependencia
        dependencia_existente = None
        if tabela == 'AUD_SQL':
            dependencia_existente = CadastroDependencias.objects.filter(
                id_aud_sql=registro_id,
                id_observacao__isnull=True
            ).first()
            if not dependencia_existente:
                dependencia_existente = CadastroDependencias.objects.filter(
                    id_aud_sql=registro_id
                ).first()
        elif tabela == 'AUD_REPORT':
            dependencia_existente = CadastroDependencias.objects.filter(
                id_aud_report=registro_id,
                id_observacao__isnull=True
            ).first()
            if not dependencia_existente:
                dependencia_existente = CadastroDependencias.objects.filter(
                    id_aud_report=registro_id
                ).first()
        elif tabela == 'AUD_FV':
            dependencia_existente = CadastroDependencias.objects.filter(
                id_aud_fv=int(registro_id),
                id_observacao__isnull=True
            ).first()
            if not dependencia_existente:
                dependencia_existente = CadastroDependencias.objects.filter(
                    id_aud_fv=int(registro_id)
                ).first()
        
        # Update existing or create new
        if dependencia_existente:
            dependencia_existente.id_observacao = observacao
            dependencia_existente.save()
            return {
                "message": "Observação adicionada à dependência existente",
                "dependencia_id": dependencia_existente.id
            }
        
        # Create new dependencia
        nova_dependencia = None
        if tabela == 'AUD_SQL':
            outro_report = CustomizacaoReport.objects.first()
            if outro_report:
                nova_dependencia = CadastroDependencias.objects.create(
                    id_aud_sql=registro_id,
                    id_aud_report=outro_report.aud_id,
                    id_observacao=observacao,
                    criado_por_id=user_id
                )
            else:
                outro_fv = CustomizacaoFV.objects.first()
                if outro_fv:
                    nova_dependencia = CadastroDependencias.objects.create(
                        id_aud_sql=registro_id,
                        id_aud_fv=outro_fv.aud_id,
                        id_observacao=observacao,
                        criado_por_id=user_id
                    )
        elif tabela == 'AUD_REPORT':
            outro_sql = CustomizacaoSQL.objects.first()
            if outro_sql:
                nova_dependencia = CadastroDependencias.objects.create(
                    id_aud_report=registro_id,
                    id_aud_sql=outro_sql.codsentenca,
                    id_observacao=observacao,
                    criado_por_id=user_id
                )
            else:
                outro_fv = CustomizacaoFV.objects.first()
                if outro_fv:
                    nova_dependencia = CadastroDependencias.objects.create(
                        id_aud_report=registro_id,
                        id_aud_fv=outro_fv.aud_id,
                        id_observacao=observacao,
                        criado_por_id=user_id
                    )
        elif tabela == 'AUD_FV':
            outro_sql = CustomizacaoSQL.objects.first()
            if outro_sql:
                nova_dependencia = CadastroDependencias.objects.create(
                    id_aud_fv=int(registro_id),
                    id_aud_sql=outro_sql.codsentenca,
                    id_observacao=observacao,
                    criado_por_id=user_id
                )
            else:
                outro_report = CustomizacaoReport.objects.first()
                if outro_report:
                    nova_dependencia = CadastroDependencias.objects.create(
                        id_aud_fv=int(registro_id),
                        id_aud_report=outro_report.aud_id,
                        id_observacao=observacao,
                        criado_por_id=user_id
                    )
        
        if not nova_dependencia:
            raise ValueError("Não foi possível criar dependência. É necessário ter pelo menos 2 registros de tabelas diferentes.")
        
        return {
            "message": "Observação adicionada com sucesso",
            "dependencia_id": nova_dependencia.id
        }
    
    def _to_dict(self, dep: CadastroDependencias) -> Dict[str, Any]:
        """Convert CadastroDependencias to dict."""
        return {
            'id': dep.id,
            'id_aud_sql': dep.id_aud_sql,
            'id_aud_report': dep.id_aud_report,
            'id_aud_fv': dep.id_aud_fv,
            'prioridade': dep.id_prioridade.nivel if dep.id_prioridade else None,
            'observacao': dep.id_observacao.texto if dep.id_observacao else None,
            'data_criacao': dep.data_criacao
        }





