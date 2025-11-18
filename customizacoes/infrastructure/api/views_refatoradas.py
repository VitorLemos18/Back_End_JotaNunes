"""
Refactored API views using Clean Architecture principles.
These views use use cases from the Application layer.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ...application.use_cases.get_historico_use_case import GetHistoricoUseCase
from ...application.use_cases.comparar_registros_use_case import CompararRegistrosUseCase
from ...application.use_cases.adicionar_observacao_use_case import AdicionarObservacaoUseCase
from ...infrastructure.repositories.aud_sql_repository import DjangoAudSQLRepository
from ...infrastructure.repositories.dependencia_repository import DjangoDependenciaRepository
from ...infrastructure.repositories.observacao_repository import DjangoObservacaoRepository


# Dependency injection - in production, use a DI container
_aud_sql_repo = DjangoAudSQLRepository()
_dependencia_repo = DjangoDependenciaRepository()
_observacao_repo = DjangoObservacaoRepository()


class HistoricoAlteracoesViewRefatorada(APIView):
    """
    Refactored view for historico de alterações.
    Uses GetHistoricoUseCase following Clean Architecture.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_case = GetHistoricoUseCase(
            aud_sql_repo=_aud_sql_repo,
            aud_report_repo=None,  # TODO: Implement
            aud_fv_repo=None,  # TODO: Implement
            dependencia_repo=_dependencia_repo
        )
    
    def get(self, request):
        """Get historico de alterações."""
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        try:
            result = self._use_case.execute(page=page, page_size=page_size)
            
            # Convert DTOs to dict for response
            results_dict = [
                {
                    'tabela': item.tabela,
                    'id': item.id,
                    'codsentenca': item.codsentenca,
                    'titulo': item.titulo,
                    'nome': item.nome,
                    'descricao': item.descricao,
                    'reccreatedby': item.reccreatedby,
                    'prioridade': item.prioridade,
                    'observacao': item.observacao,
                    'data_criacao': item.data_criacao.isoformat() if item.data_criacao else None
                }
                for item in result.results
            ]
            
            return Response({
                'count': result.count,
                'next': result.next,
                'previous': result.previous,
                'results': results_dict
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompararRegistrosViewRefatorada(APIView):
    """
    Refactored view for comparing registros.
    Uses CompararRegistrosUseCase following Clean Architecture.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_case = CompararRegistrosUseCase(
            aud_sql_repo=_aud_sql_repo,
            aud_report_repo=None,  # TODO: Implement
            aud_fv_repo=None,  # TODO: Implement
            dependencia_repo=_dependencia_repo
        )
    
    def get(self, request):
        """Compare current and previous registro."""
        tabela = request.query_params.get('tabela', '').upper()
        registro_id = request.query_params.get('id')
        
        if not tabela or not registro_id:
            return Response(
                {"error": "Campos obrigatórios: tabela, id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self._use_case.execute(tabela=tabela, registro_id=registro_id)
            
            # Convert DTOs to dict for response
            registro_atual_dict = {
                'id': result.registro_atual.id,
                'codsentenca': result.registro_atual.codsentenca,
                'titulo': result.registro_atual.titulo,
                'sentenca': result.registro_atual.sentenca,
                'aplicacao': result.registro_atual.aplicacao,
                'tamanho': result.registro_atual.tamanho,
                'codigo': result.registro_atual.codigo,
                'descricao': result.registro_atual.descricao,
                'nome': result.registro_atual.nome,
                'idcategoria': result.registro_atual.idcategoria,
                'ativo': result.registro_atual.ativo,
                'reccreatedby': result.registro_atual.reccreatedby,
                'reccreatedon': result.registro_atual.reccreatedon.isoformat() if result.registro_atual.reccreatedon else None,
                'observacao': result.registro_atual.observacao
            }
            
            registro_anterior_dict = None
            if result.registro_anterior:
                registro_anterior_dict = {
                    'id': result.registro_anterior.id,
                    'codsentenca': result.registro_anterior.codsentenca,
                    'titulo': result.registro_anterior.titulo,
                    'sentenca': result.registro_anterior.sentenca,
                    'aplicacao': result.registro_anterior.aplicacao,
                    'tamanho': result.registro_anterior.tamanho,
                    'codigo': result.registro_anterior.codigo,
                    'descricao': result.registro_anterior.descricao,
                    'nome': result.registro_anterior.nome,
                    'idcategoria': result.registro_anterior.idcategoria,
                    'ativo': result.registro_anterior.ativo,
                    'reccreatedby': result.registro_anterior.reccreatedby,
                    'reccreatedon': result.registro_anterior.reccreatedon.isoformat() if result.registro_anterior.reccreatedon else None,
                    'observacao': result.registro_anterior.observacao
                }
            
            return Response({
                'tabela': result.tabela,
                'registro_atual': registro_atual_dict,
                'registro_anterior': registro_anterior_dict
            })
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Erro ao buscar registros: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdicionarObservacaoRegistroViewRefatorada(APIView):
    """
    Refactored view for adding observation.
    Uses AdicionarObservacaoUseCase following Clean Architecture.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._use_case = AdicionarObservacaoUseCase(
            observacao_repo=_observacao_repo,
            dependencia_repo=_dependencia_repo
        )
    
    def post(self, request):
        """Add observation to registro."""
        tabela = request.data.get('tabela')
        registro_id = request.data.get('id')
        texto = request.data.get('texto')
        
        if not tabela or not registro_id or not texto:
            return Response(
                {"error": "Campos obrigatórios: tabela, id, texto"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            result = self._use_case.execute(
                tabela=tabela,
                registro_id=str(registro_id),
                texto=texto,
                user_id=request.user.id
            )
            
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





