# customizacoes/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport,
    CadastroDependencias
)
from .serializers import *


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# READ-ONLY
class CustomizacaoFVViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomizacaoFV.objects.all().order_by('nome')
    serializer_class = CustomizacaoFVSerializer
    pagination_class = StandardPagination


class CustomizacaoSQLViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomizacaoSQL.objects.all().order_by('titulo')
    serializer_class = CustomizacaoSQLSerializer
    pagination_class = StandardPagination


class CustomizacaoReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CustomizacaoReport.objects.all().order_by('codigo')
    serializer_class = CustomizacaoReportSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        # Retorna todos os registros ordenados por código
        # Filtro de IDs numéricos removido para compatibilidade com SQL Server
        return CustomizacaoReport.objects.all().order_by('codigo')


# CRUD
# REMOVIDO: Prioridade, Observacao e Notificacao não existem mais no banco
# class PrioridadeViewSet(viewsets.ModelViewSet):
#     queryset = Prioridade.objects.all()
#     serializer_class = PrioridadeSerializer
#
#
# class ObservacaoViewSet(viewsets.ModelViewSet):
#     queryset = Observacao.objects.all()
#     serializer_class = ObservacaoSerializer
#
#     def perform_create(self, serializer):
#         serializer.save(criado_por=self.request.user)
#
#
# class NotificacaoViewSet(viewsets.ModelViewSet):
#     queryset = Notificacao.objects.all()  # OBRIGATÓRIO
#     serializer_class = NotificacaoSerializer
#
#     def get_queryset(self):
#         # Filtra apenas notificações do usuário logado
#         return super().get_queryset().filter(id_usuario=self.request.user)
#
#     @action(detail=True, methods=['post'])
#     def marcar_lida(self, request, pk=None):
#         notif = self.get_object()
#         notif.lida = True
#         notif.save()
#         return Response({'status': 'marcada como lida'})


class CadastroDependenciasViewSet(viewsets.ModelViewSet):
    queryset = CadastroDependencias.objects.all()  # Removido select_related pois id_prioridade não existe mais
    serializer_class = CadastroDependenciasSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-data_criacao')
        
        # Filtro por tabela de origem ou destino
        origem_tabela = self.request.query_params.get('origem_tabela')
        if origem_tabela:
            # Filtra dependências onde a origem ou destino é da tabela especificada
            if origem_tabela == 'AUD_SQL':
                queryset = queryset.filter(id_aud_sql__isnull=False)
            elif origem_tabela == 'AUD_Report':
                queryset = queryset.filter(id_aud_report__isnull=False)
            elif origem_tabela == 'AUD_FV':
                queryset = queryset.filter(id_aud_fv__isnull=False)
        
        # Filtro por prioridade
        prioridade = self.request.query_params.get('prioridade')
        sem_prioridade = self.request.query_params.get('sem_prioridade')
        
        if prioridade or sem_prioridade:
            from .models import CustomizacaoSQL, CustomizacaoReport, CustomizacaoFV
            
            def _determinar_origem_destino(dep):
                """Determina qual campo é origem e qual é destino (mesma lógica do serializer)"""
                origem_tipo = None
                destino_tipo = None
                
                if dep.id_aud_sql and dep.id_aud_report:
                    origem_tipo = 'sql'
                    destino_tipo = 'report'
                elif dep.id_aud_sql and dep.id_aud_fv:
                    origem_tipo = 'sql'
                    destino_tipo = 'fv'
                elif dep.id_aud_report and dep.id_aud_sql:
                    origem_tipo = 'report'
                    destino_tipo = 'sql'
                elif dep.id_aud_report and dep.id_aud_fv:
                    origem_tipo = 'report'
                    destino_tipo = 'fv'
                elif dep.id_aud_fv and dep.id_aud_sql:
                    origem_tipo = 'fv'
                    destino_tipo = 'sql'
                elif dep.id_aud_fv and dep.id_aud_report:
                    origem_tipo = 'fv'
                    destino_tipo = 'report'
                
                return origem_tipo, destino_tipo
            
            def _obter_prioridade(dep, origem_tipo, destino_tipo):
                """Obtém a prioridade da origem, ou do destino se origem não tiver (mesma lógica do serializer)"""
                # Tenta buscar a prioridade da origem primeiro
                try:
                    if origem_tipo == 'sql' and dep.id_aud_sql:
                        sql = CustomizacaoSQL.objects.get(codsentenca=dep.id_aud_sql)
                        if sql.prioridade:
                            return sql.prioridade
                    elif origem_tipo == 'report' and dep.id_aud_report:
                        report = CustomizacaoReport.objects.get(id=dep.id_aud_report)
                        if report.prioridade:
                            return report.prioridade
                    elif origem_tipo == 'fv' and dep.id_aud_fv:
                        fv = CustomizacaoFV.objects.get(id=dep.id_aud_fv)
                        if fv.prioridade:
                            return fv.prioridade
                except Exception:
                    pass
                
                # Se origem não tiver prioridade, tenta buscar do destino
                try:
                    if destino_tipo == 'sql' and dep.id_aud_sql and origem_tipo != 'sql':
                        sql = CustomizacaoSQL.objects.get(codsentenca=dep.id_aud_sql)
                        if sql.prioridade:
                            return sql.prioridade
                    elif destino_tipo == 'report' and dep.id_aud_report and origem_tipo != 'report':
                        report = CustomizacaoReport.objects.get(id=dep.id_aud_report)
                        if report.prioridade:
                            return report.prioridade
                    elif destino_tipo == 'fv' and dep.id_aud_fv and origem_tipo != 'fv':
                        fv = CustomizacaoFV.objects.get(id=dep.id_aud_fv)
                        if fv.prioridade:
                            return fv.prioridade
                except Exception:
                    pass
                
                return None
            
            # Lista para armazenar IDs de dependências que atendem ao filtro
            ids_filtrados = []
            
            # Itera sobre todas as dependências para verificar a prioridade
            for dep in queryset:
                origem_tipo, destino_tipo = _determinar_origem_destino(dep)
                if not origem_tipo or not destino_tipo:
                    continue
                
                prioridade_final = _obter_prioridade(dep, origem_tipo, destino_tipo)
                
                # Verifica se atende ao filtro
                if sem_prioridade == 'true':
                    # Filtra por "Sem Prioridade" - quando não há prioridade ou está vazia
                    if not prioridade_final or (isinstance(prioridade_final, str) and prioridade_final.strip() == ''):
                        ids_filtrados.append(dep.id)
                elif prioridade:
                    # Filtra por prioridade específica
                    if prioridade_final == prioridade:
                        ids_filtrados.append(dep.id)
            
            # Aplica o filtro pelos IDs encontrados
            queryset = queryset.filter(id__in=ids_filtrados)
        
        # Filtro por busca (nome, ID ou usuário)
        search = self.request.query_params.get('search')
        if search:
            # Busca em origem_nome, destino_nome, origem_id, destino_id ou criado_por_nome
            # Como esses campos são calculados no serializer, precisamos fazer uma busca mais ampla
            # Busca por ID nas tabelas relacionadas
            from django.db.models import Q
            queryset = queryset.filter(
                Q(id_aud_sql__icontains=search) |
                Q(id_aud_report__icontains=search) |
                Q(id_aud_fv__icontains=search) |
                Q(criado_por__icontains=search)
            )
        
        return queryset

    def perform_create(self, serializer):
        # Salva com o ID do usuário ao invés do objeto User
        user_id = getattr(self.request.user, 'id', None) if self.request.user.is_authenticated else None
        serializer.save(criado_por=user_id)

    def _obter_prioridade_maior(self, prioridade_atual, prioridade_nova):
        """
        Compara duas prioridades e retorna a maior.
        Hierarquia: Alta > Média > Baixa
        """
        if not prioridade_nova:
            return prioridade_atual
        
        if not prioridade_atual:
            return prioridade_nova
        
        hierarquia = {'Alta': 3, 'Média': 2, 'Baixa': 1}
        nivel_atual = hierarquia.get(prioridade_atual, 0)
        nivel_novo = hierarquia.get(prioridade_nova, 0)
        
        return prioridade_nova if nivel_novo >= nivel_atual else prioridade_atual
    
    def _atualizar_prioridade_registro(self, tipo, registro_id, nova_prioridade):
        """
        Atualiza a prioridade de um registro, mantendo a maior se já existir uma.
        """
        try:
            if tipo == 'sql':
                registro = CustomizacaoSQL.objects.filter(codsentenca=registro_id).first()
                if registro:
                    prioridade_final = self._obter_prioridade_maior(registro.prioridade, nova_prioridade)
                    registro.prioridade = prioridade_final
                    registro.save()
            elif tipo == 'report':
                registro = CustomizacaoReport.objects.filter(id=registro_id).first()
                if registro:
                    prioridade_final = self._obter_prioridade_maior(registro.prioridade, nova_prioridade)
                    registro.prioridade = prioridade_final
                    registro.save()
            elif tipo == 'fv':
                registro = CustomizacaoFV.objects.filter(id=registro_id).first()
                if registro:
                    prioridade_final = self._obter_prioridade_maior(registro.prioridade, nova_prioridade)
                    registro.prioridade = prioridade_final
                    registro.save()
        except Exception as e:
            # Log do erro mas continua o processo
            pass

    @action(detail=False, methods=['post'], url_path='criar-multiplas')
    def criar_multiplas(self, request):
        origem_tipo = request.data.get('origem_tipo')
        origem_id = request.data.get('origem_id')
        destinos = request.data.get('destinos', [])
        prioridade = request.data.get('prioridade')  # Recebe a prioridade do frontend

        if origem_tipo not in ['sql', 'report', 'fv'] or not origem_id:
            return Response({"error": "Origem inválida."}, status=status.HTTP_400_BAD_REQUEST)
        if not destinos:
            return Response({"error": "Pelo menos 1 destino é necessário."}, status=status.HTTP_400_BAD_REQUEST)

        # Valida prioridade se fornecida
        if prioridade and prioridade not in ['Alta', 'Média', 'Baixa']:
            return Response({"error": "Prioridade inválida. Use: Alta, Média ou Baixa."}, status=status.HTTP_400_BAD_REQUEST)

        # Valida que origem e destino são de tipos diferentes
        created = []
        with transaction.atomic():
            # Atualiza prioridade na origem se fornecida (mantém a maior se já existir)
            if prioridade:
                self._atualizar_prioridade_registro(origem_tipo, origem_id, prioridade)

            # Coleta todos os IDs de destino para atualizar prioridade depois
            destinos_ids = []
            
            for dest in destinos:
                dest_tipo = dest.get('tipo')
                dest_id = dest.get('id')
                if dest_tipo not in ['sql', 'report', 'fv']:
                    continue
                
                # Valida que origem e destino são de tipos diferentes
                if origem_tipo == dest_tipo:
                    continue  # Pula se origem e destino são do mesmo tipo

                data = {
                    'id_aud_sql': None,
                    'id_aud_report': None,
                    'id_aud_fv': None,
                    'criado_por': getattr(request.user, 'id', None) if request.user.is_authenticated else None
                }

                # Origem
                if origem_tipo == 'sql':
                    data['id_aud_sql'] = origem_id
                elif origem_tipo == 'report':
                    data['id_aud_report'] = origem_id
                elif origem_tipo == 'fv':
                    data['id_aud_fv'] = origem_id

                # Destino (só preenche se for diferente da origem)
                if dest_tipo == 'sql':
                    data['id_aud_sql'] = dest_id
                elif dest_tipo == 'report':
                    data['id_aud_report'] = dest_id
                elif dest_tipo == 'fv':
                    data['id_aud_fv'] = dest_id

                # Valida que exatamente 2 campos estão preenchidos
                campos_preenchidos = sum(1 for v in [data['id_aud_sql'], data['id_aud_report'], data['id_aud_fv']] if v is not None)
                if campos_preenchidos != 2:
                    continue  # Pula se não tiver exatamente 2 campos

                try:
                    dep = CadastroDependencias(**data)
                    dep.full_clean()
                    dep.save()
                    created.append(dep.id)
                    
                    # Adiciona à lista de destinos para atualizar prioridade depois
                    destinos_ids.append((dest_tipo, dest_id))
                            
                except ValidationError as e:
                    # Se houver erro de validação, continua para o próximo destino
                    continue

            # Atualiza prioridade em TODOS os destinos após criar as dependências
            # Isso garante que todos recebam a prioridade, mesmo se houver erro em algum
            if prioridade:
                for dest_tipo, dest_id in destinos_ids:
                    self._atualizar_prioridade_registro(dest_tipo, dest_id, prioridade)

        # Notificação removida - tabela Notificacao não existe mais no banco

        return Response({
            "criadas": len(created),
            "ids": created
        }, status=status.HTTP_201_CREATED)


# Insights - Endpoints de contagem
class InsightsFVView(APIView):
    def get(self, request):
        try:
            count = CustomizacaoFV.objects.count()
            return Response({"count": count})
        except Exception as e:
            return Response({"error": str(e), "count": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsightsSQLView(APIView):
    def get(self, request):
        try:
            count = CustomizacaoSQL.objects.count()
            return Response({"count": count})
        except Exception as e:
            return Response({"error": str(e), "count": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsightsReportView(APIView):
    def get(self, request):
        # Conta todos os registros (filtro de IDs numéricos removido para compatibilidade)
        try:
            count = CustomizacaoReport.objects.count()
            return Response({"count": count})
        except Exception as e:
            # Se houver erro, tenta filtrar apenas IDs válidos
            try:
                count = CustomizacaoReport.objects.exclude(id__isnull=True).count()
                return Response({"count": count})
            except Exception as e2:
                return Response({"error": str(e2), "count": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsightsDependenciasView(APIView):
    def get(self, request):
        try:
            count = CadastroDependencias.objects.count()
            return Response({"count": count})
        except Exception as e:
            return Response({"error": str(e), "count": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InsightsPrioridadesView(APIView):
    def get(self, request):
        try:
            # Conta registros por nível de prioridade nas tabelas AUD
            from collections import Counter
            
            # Busca prioridades de todas as tabelas AUD
            prioridades_sql = CustomizacaoSQL.objects.exclude(prioridade__isnull=True).exclude(prioridade='').values_list('prioridade', flat=True)
            prioridades_report = CustomizacaoReport.objects.exclude(prioridade__isnull=True).exclude(prioridade='').values_list('prioridade', flat=True)
            prioridades_fv = CustomizacaoFV.objects.exclude(prioridade__isnull=True).exclude(prioridade='').values_list('prioridade', flat=True)
            
            # Conta todas as prioridades
            todas_prioridades = list(prioridades_sql) + list(prioridades_report) + list(prioridades_fv)
            contador = Counter(todas_prioridades)
            
            # Cria um dicionário com as contagens
            result = dict(contador)
            
            # Conta registros sem prioridade
            sem_prioridade_sql = CustomizacaoSQL.objects.filter(Q(prioridade__isnull=True) | Q(prioridade='')).count()
            sem_prioridade_report = CustomizacaoReport.objects.filter(Q(prioridade__isnull=True) | Q(prioridade='')).count()
            sem_prioridade_fv = CustomizacaoFV.objects.filter(Q(prioridade__isnull=True) | Q(prioridade='')).count()
            sem_prioridade = sem_prioridade_sql + sem_prioridade_report + sem_prioridade_fv
            
            if sem_prioridade > 0:
                result['Sem Prioridade'] = sem_prioridade
            
            result['total'] = sum(result.values())
            return Response(result)
        except Exception as e:
            return Response({"error": str(e), "Alta": 0, "Média": 0, "Baixa": 0, "total": 0}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistrosModalView(APIView):
    """
    Endpoint para buscar registros formatados para o modal de dependências.
    Retorna registros de uma tabela específica (AUD_SQL, AUD_Report, AUD_FV)
    no formato: { user, tabela, campo, id }
    """
    def get(self, request):
        tabela = request.query_params.get('tabela', '').upper()
        
        if tabela == 'AUD_SQL':
            registros = CustomizacaoSQL.objects.all().order_by('titulo')
            dados = []
            for reg in registros:
                dados.append({
                    'id': reg.codsentenca,
                    'user': reg.reccreatedby or 'N/A',
                    'tabela': 'AUD_SQL',
                    'campo': reg.titulo or reg.codsentenca,
                    'codigo': reg.codsentenca,
                    'titulo': reg.titulo,
                    'sentenca': reg.sentenca
                })
            return Response(dados)
        
        elif tabela == 'AUD_REPORT':
            registros = CustomizacaoReport.objects.all().order_by('codigo')
            dados = []
            for reg in registros:
                dados.append({
                    'id': reg.id,
                    'user': reg.reccreatedby or 'N/A',
                    'tabela': 'AUD_Report',
                    'campo': reg.codigo or str(reg.id),
                    'codigo': reg.codigo,
                    'descricao': reg.descricao
                })
            return Response(dados)
        
        elif tabela == 'AUD_FV':
            registros = CustomizacaoFV.objects.all().order_by('nome')
            dados = []
            for reg in registros:
                dados.append({
                    'id': reg.id,
                    'user': reg.reccreatedby or 'N/A',
                    'tabela': 'AUD_FV',
                    'campo': reg.nome or str(reg.id),
                    'nome': reg.nome,
                    'descricao': reg.descricao
                })
            return Response(dados)
        
        return Response({"error": "Tabela inválida. Use: AUD_SQL, AUD_Report ou AUD_FV"}, status=status.HTTP_400_BAD_REQUEST)


class HistoricoAlteracoesView(APIView):
    """
    Endpoint para buscar histórico de alterações de todas as tabelas AUD.
    Retorna registros de AUD_SQL, AUD_REPORT e AUD_FV com prioridade relacionada (se houver).
    """
    def get(self, request):
        from django.db import connection
        from datetime import datetime
        
        # Obtém filtros da query string
        data_inicio = request.query_params.get('data_inicio')
        data_fim = request.query_params.get('data_fim')
        filtro_tabela = request.query_params.get('tabela')
        
        # Converte datas se fornecidas
        data_inicio_dt = None
        data_fim_dt = None
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            except ValueError:
                pass
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                # Adiciona 23:59:59 para incluir o dia inteiro
                data_fim_dt = data_fim_dt.replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
        
        # Busca prioridades e observações diretamente das tabelas AUD
        # Mapeia prioridades por ID de cada tabela
        prioridades_sql = {}
        prioridades_report = {}
        prioridades_fv = {}
        
        # Mapeia observações por ID de cada tabela
        observacoes_sql = {}
        observacoes_report = {}
        observacoes_fv = {}
        
        # Busca registros SQL
        for sql in CustomizacaoSQL.objects.all():
            if sql.prioridade:
                prioridades_sql[sql.codsentenca] = sql.prioridade
            if sql.observacao:
                observacoes_sql[sql.codsentenca] = sql.observacao
        
        # Busca registros REPORT
        for report in CustomizacaoReport.objects.all():
            if report.prioridade:
                prioridades_report[report.id] = report.prioridade
            if report.observacao:
                observacoes_report[report.id] = report.observacao
        
        # Busca registros FV
        for fv in CustomizacaoFV.objects.all():
            if fv.prioridade:
                prioridades_fv[fv.id] = fv.prioridade
            if fv.observacao:
                observacoes_fv[fv.id] = fv.observacao
        
        historico = []
        
        # AUD_SQL: CODSENTENCA, RECMODIFIEDBY (ou RECCREATEDBY), TITULO
        if not filtro_tabela or filtro_tabela == 'AUD_SQL':
            with connection.cursor() as cursor:
                # Monta query com filtros de data se necessário
                query = """
                    SELECT CODSENTENCA, TITULO, RECCREATEDBY, RECCREATEDON, 
                           RECMODIFIEDBY, RECMODIFIEDON
                    FROM AUD_SQL
                    WHERE 1=1
                """
                params = []
                
                if data_inicio_dt:
                    query += " AND (RECCREATEDON >= %s OR RECMODIFIEDON >= %s)"
                    params.extend([data_inicio_dt, data_inicio_dt])
                
                if data_fim_dt:
                    query += " AND (RECCREATEDON <= %s OR RECMODIFIEDON <= %s OR RECCREATEDON IS NULL)"
                    params.extend([data_fim_dt, data_fim_dt])
                
                query += " ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    codsentenca = row[0]
                    titulo = row[1] if len(row) > 1 else None
                    reccreatedby = row[2] if len(row) > 2 else None
                    reccreatedon = row[3] if len(row) > 3 else None
                    recmodifiedby = row[4] if len(row) > 4 else None
                    recmodifiedon = row[5] if len(row) > 5 else None
                    
                    # Filtra por data se necessário (filtro adicional no Python para garantir)
                    data_referencia = recmodifiedon if recmodifiedon else reccreatedon
                    if data_referencia:
                        if data_inicio_dt and data_referencia < data_inicio_dt:
                            continue
                        if data_fim_dt and data_referencia > data_fim_dt:
                            continue
                    
                    # Usa RECMODIFIEDBY se existir, senão usa RECCREATEDBY
                    usuario = recmodifiedby if recmodifiedby else (reccreatedby or 'N/A')
                    
                    historico.append({
                        'tabela': 'AUD_SQL',
                        'id': codsentenca,
                        'codsentenca': codsentenca,
                        'reccreatedby': usuario,
                        'titulo': titulo or 'N/A',
                        'prioridade': prioridades_sql.get(codsentenca),
                        'observacao': observacoes_sql.get(codsentenca),
                        'data_criacao': reccreatedon.isoformat() if reccreatedon and hasattr(reccreatedon, 'isoformat') else (str(reccreatedon) if reccreatedon else None),
                        'data_modificacao': recmodifiedon.isoformat() if recmodifiedon and hasattr(recmodifiedon, 'isoformat') else (str(recmodifiedon) if recmodifiedon else None)
                    })
        
        # AUD_REPORT: ID, RECMODIFIEDBY (ou RECCREATEDBY), DESCRICAO
        if not filtro_tabela or filtro_tabela == 'AUD_REPORT':
            with connection.cursor() as cursor:
                query = """
                    SELECT ID, DESCRICAO, RECCREATEDBY, RECCREATEDON, 
                           RECMODIFIEDBY, RECMODIFIEDON
                    FROM AUD_REPORT
                    WHERE 1=1
                """
                params = []
                
                if data_inicio_dt:
                    query += " AND (RECCREATEDON >= %s OR RECMODIFIEDON >= %s)"
                    params.extend([data_inicio_dt, data_inicio_dt])
                
                if data_fim_dt:
                    query += " AND (RECCREATEDON <= %s OR RECMODIFIEDON <= %s OR RECCREATEDON IS NULL)"
                    params.extend([data_fim_dt, data_fim_dt])
                
                query += " ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    aud_id = row[0]
                    descricao = row[1] if len(row) > 1 else None
                    reccreatedby = row[2] if len(row) > 2 else None
                    reccreatedon = row[3] if len(row) > 3 else None
                    recmodifiedby = row[4] if len(row) > 4 else None
                    recmodifiedon = row[5] if len(row) > 5 else None
                    
                    # Filtra por data se necessário
                    data_referencia = recmodifiedon if recmodifiedon else reccreatedon
                    if data_referencia:
                        if data_inicio_dt and data_referencia < data_inicio_dt:
                            continue
                        if data_fim_dt and data_referencia > data_fim_dt:
                            continue
                    
                    # Usa RECMODIFIEDBY se existir, senão usa RECCREATEDBY
                    usuario = recmodifiedby if recmodifiedby else (reccreatedby or 'N/A')
                    
                    historico.append({
                        'tabela': 'AUD_REPORT',
                        'id': aud_id,
                        'descricao': descricao or 'N/A',
                        'reccreatedby': usuario,
                        'prioridade': prioridades_report.get(aud_id),
                        'observacao': observacoes_report.get(aud_id),
                        'data_criacao': reccreatedon.isoformat() if reccreatedon and hasattr(reccreatedon, 'isoformat') else (str(reccreatedon) if reccreatedon else None),
                        'data_modificacao': recmodifiedon.isoformat() if recmodifiedon and hasattr(recmodifiedon, 'isoformat') else (str(recmodifiedon) if recmodifiedon else None)
                    })
        
        # AUD_FV: ID, RECMODIFIEDBY (ou RECCREATEDBY), NOME
        if not filtro_tabela or filtro_tabela == 'AUD_FV':
            with connection.cursor() as cursor:
                query = """
                    SELECT ID, NOME, RECCREATEDBY, RECCREATEDON, 
                           RECMODIFIEDBY, RECMODIFIEDON
                    FROM AUD_FV
                    WHERE 1=1
                """
                params = []
                
                if data_inicio_dt:
                    query += " AND (RECCREATEDON >= %s OR RECMODIFIEDON >= %s)"
                    params.extend([data_inicio_dt, data_inicio_dt])
                
                if data_fim_dt:
                    query += " AND (RECCREATEDON <= %s OR RECMODIFIEDON <= %s OR RECCREATEDON IS NULL)"
                    params.extend([data_fim_dt, data_fim_dt])
                
                query += " ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    aud_id = row[0]
                    nome = row[1] if len(row) > 1 else None
                    reccreatedby = row[2] if len(row) > 2 else None
                    reccreatedon = row[3] if len(row) > 3 else None
                    recmodifiedby = row[4] if len(row) > 4 else None
                    recmodifiedon = row[5] if len(row) > 5 else None
                    
                    # Filtra por data se necessário
                    data_referencia = recmodifiedon if recmodifiedon else reccreatedon
                    if data_referencia:
                        if data_inicio_dt and data_referencia < data_inicio_dt:
                            continue
                        if data_fim_dt and data_referencia > data_fim_dt:
                            continue
                    
                    # Usa RECMODIFIEDBY se existir, senão usa RECCREATEDBY
                    usuario = recmodifiedby if recmodifiedby else (reccreatedby or 'N/A')
                    
                    historico.append({
                        'tabela': 'AUD_FV',
                        'id': aud_id,
                        'nome': nome or 'N/A',
                        'reccreatedby': usuario,
                        'prioridade': prioridades_fv.get(aud_id),
                        'observacao': observacoes_fv.get(aud_id),
                        'data_criacao': reccreatedon.isoformat() if reccreatedon and hasattr(reccreatedon, 'isoformat') else (str(reccreatedon) if reccreatedon else None),
                        'data_modificacao': recmodifiedon.isoformat() if recmodifiedon and hasattr(recmodifiedon, 'isoformat') else (str(recmodifiedon) if recmodifiedon else None)
                    })
        
        # Ordena por data de criação (mais recente primeiro)
        historico.sort(key=lambda x: x['data_criacao'] or '', reverse=True)
        
        # Paginação
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        total = len(historico)
        results = historico[start:end]
        
        return Response({
            'count': total,
            'next': f'?page={page + 1}&page_size={page_size}' if end < total else None,
            'previous': f'?page={page - 1}&page_size={page_size}' if page > 1 else None,
            'results': results
        })


class AdicionarObservacaoRegistroView(APIView):
    """
    Endpoint para adicionar observação a um registro específico das tabelas AUD.
    Atualiza diretamente o campo observacao na tabela AUD correspondente.
    """
    def post(self, request):
        tabela = request.data.get('tabela')
        registro_id = request.data.get('id')
        texto_observacao = request.data.get('texto')
        prioridade = request.data.get('prioridade')  # Opcional: também pode atualizar prioridade
        
        if not tabela or not registro_id or not texto_observacao:
            return Response(
                {"error": "Campos obrigatórios: tabela, id, texto"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Atualiza o campo observacao diretamente na tabela AUD
            if tabela == 'AUD_SQL':
                registro = CustomizacaoSQL.objects.get(codsentenca=registro_id)
                registro.observacao = texto_observacao
                if prioridade:
                    registro.prioridade = prioridade
                registro.save()
            elif tabela == 'AUD_REPORT':
                registro = CustomizacaoReport.objects.get(id=registro_id)
                registro.observacao = texto_observacao
                if prioridade:
                    registro.prioridade = prioridade
                registro.save()
            elif tabela == 'AUD_FV':
                registro = CustomizacaoFV.objects.get(id=registro_id)
                registro.observacao = texto_observacao
                if prioridade:
                    registro.prioridade = prioridade
                registro.save()
            else:
                return Response(
                    {"error": "Tabela inválida. Use: AUD_SQL, AUD_REPORT ou AUD_FV"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                "success": True,
                "message": "Observação adicionada com sucesso",
                "tabela": tabela,
                "id": registro_id
            })
        except CustomizacaoSQL.DoesNotExist:
            return Response(
                {"error": f"Registro não encontrado na tabela {tabela} com ID {registro_id}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except CustomizacaoReport.DoesNotExist:
            return Response(
                {"error": f"Registro não encontrado na tabela {tabela} com ID {registro_id}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except CustomizacaoFV.DoesNotExist:
            return Response(
                {"error": f"Registro não encontrado na tabela {tabela} com ID {registro_id}"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Erro inesperado: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompararRegistrosView(APIView):
    """
    Endpoint para buscar um registro e seu anterior para comparação.
    Retorna o registro atual e o anterior (se existir) para identificar alterações.
    """
    def get(self, request):
        tabela = request.query_params.get('tabela', '').upper()
        registro_id = request.query_params.get('id')
        data_modificacao = request.query_params.get('data_modificacao')  # Data de modificação do registro selecionado
        
        if not tabela or not registro_id:
            return Response(
                {"error": "Campos obrigatórios: tabela, id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.db import connection
        from datetime import datetime, timedelta
        
        registro_atual = None
        registro_anterior = None
        
        try:
            if tabela == 'AUD_SQL':
                # AUD_SQL não tem campo 'id' separado, o identificador é o próprio CODSENTENCA
                # O parâmetro 'registro_id' recebido contém o CODSENTENCA
                # Usa raw SQL para buscar o registro atual (específico ou mais recente) e anterior
                try:
                    with connection.cursor() as cursor:
                        # Busca TODOS os registros com o mesmo CODSENTENCA, ordenados por data DESC
                        # Inclui RECMODIFIEDON para poder filtrar pela data de modificação
                        cursor.execute("""
                            SELECT CODSENTENCA, TITULO, SENTENCA, APLICACAO, TAMANHO, 
                                   RECCREATEDBY, RECCREATEDON, RECMODIFIEDBY, RECMODIFIEDON,
                                   PRIORIDADE, OBSERVACAO
                            FROM AUD_SQL 
                            WHERE CODSENTENCA = %s 
                            ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC
                        """, [registro_id])
                        
                        rows = cursor.fetchall()
                        
                        if not rows or len(rows) == 0:
                            return Response(
                                {"error": "Registro não encontrado"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                        
                        # Se data_modificacao foi fornecida, busca o registro específico
                        indice_atual = 0
                        if data_modificacao:
                            try:
                                # Converte a data de modificação para comparar
                                # Remove timezone e microsegundos se houver
                                import re
                                # Formato esperado: 2025-10-09T13:39:33.000 ou 2025-10-09 13:39:33
                                data_mod_str = data_modificacao.replace('T', ' ')
                                # Remove microsegundos e timezone
                                data_mod_str = re.sub(r'\.\d+', '', data_mod_str)  # Remove .000
                                data_mod_str = re.sub(r'[+-]\d{2}:\d{2}$', '', data_mod_str)  # Remove +00:00
                                data_mod_str = data_mod_str.strip()
                                if len(data_mod_str) > 19:
                                    data_mod_str = data_mod_str[:19]
                                data_mod = datetime.strptime(data_mod_str, '%Y-%m-%d %H:%M:%S')
                                
                                # Encontra o índice do registro com a data de modificação correspondente
                                for idx, row in enumerate(rows):
                                    recmodifiedon = row[8] if len(row) > 8 else None
                                    reccreatedon = row[6] if len(row) > 6 else None
                                    
                                    # Compara a data de modificação (ou criação se não houver modificação)
                                    data_registro = recmodifiedon if recmodifiedon else reccreatedon
                                    if data_registro:
                                        # Compara apenas data e hora (sem microsegundos)
                                        if hasattr(data_registro, 'replace'):
                                            data_registro_clean = data_registro.replace(microsecond=0)
                                        else:
                                            data_registro_clean = data_registro
                                        
                                        # Compara apenas até o segundo (sem microsegundos)
                                        if isinstance(data_registro_clean, datetime):
                                            data_registro_compare = data_registro_clean.replace(microsecond=0)
                                        else:
                                            data_registro_compare = data_registro_clean
                                        
                                        if data_registro_compare == data_mod:
                                            indice_atual = idx
                                            break
                            except (ValueError, AttributeError) as e:
                                # Se houver erro ao parsear a data, usa o primeiro registro (mais recente)
                                pass
                        
                        # Registro atual = registro no índice encontrado
                        row_atual = rows[indice_atual]
                        reccreatedby_atual = row_atual[7] if len(row_atual) > 7 and row_atual[7] else (row_atual[5] if len(row_atual) > 5 else None)
                        recmodifiedon_atual = row_atual[8] if len(row_atual) > 8 else None
                        registro_atual = {
                            'id': row_atual[0],
                            'codsentenca': row_atual[0],
                            'titulo': row_atual[1] if len(row_atual) > 1 else None,
                            'sentenca': row_atual[2] if len(row_atual) > 2 else None,
                            'aplicacao': row_atual[3] if len(row_atual) > 3 else None,
                            'tamanho': row_atual[4] if len(row_atual) > 4 else None,
                            'reccreatedby': reccreatedby_atual,
                            'reccreatedon': row_atual[6].isoformat() if len(row_atual) > 6 and row_atual[6] and hasattr(row_atual[6], 'isoformat') else (str(row_atual[6]) if len(row_atual) > 6 and row_atual[6] else None),
                            'recmmodifiedon': recmodifiedon_atual.isoformat() if recmodifiedon_atual and hasattr(recmodifiedon_atual, 'isoformat') else (str(recmodifiedon_atual) if recmodifiedon_atual else None),
                            'prioridade': row_atual[9] if len(row_atual) > 9 else None,
                            'observacao': row_atual[10] if len(row_atual) > 10 else None
                        }
                        
                        # Registro anterior = registro imediatamente anterior ao atual (se existir)
                        if indice_atual + 1 < len(rows):
                            row_anterior = rows[indice_atual + 1]
                            reccreatedby_anterior = row_anterior[7] if len(row_anterior) > 7 and row_anterior[7] else (row_anterior[5] if len(row_anterior) > 5 else None)
                            recmodifiedon_anterior = row_anterior[8] if len(row_anterior) > 8 else None
                            registro_anterior = {
                                'id': row_anterior[0],
                                'codsentenca': row_anterior[0],
                                'titulo': row_anterior[1] if len(row_anterior) > 1 else None,
                                'sentenca': row_anterior[2] if len(row_anterior) > 2 else None,
                                'aplicacao': row_anterior[3] if len(row_anterior) > 3 else None,
                                'tamanho': row_anterior[4] if len(row_anterior) > 4 else None,
                                'reccreatedby': reccreatedby_anterior,
                                'reccreatedon': row_anterior[6].isoformat() if len(row_anterior) > 6 and row_anterior[6] and hasattr(row_anterior[6], 'isoformat') else (str(row_anterior[6]) if len(row_anterior) > 6 and row_anterior[6] else None),
                                'recmmodifiedon': recmodifiedon_anterior.isoformat() if recmodifiedon_anterior and hasattr(recmodifiedon_anterior, 'isoformat') else (str(recmodifiedon_anterior) if recmodifiedon_anterior else None),
                                'prioridade': row_anterior[9] if len(row_anterior) > 9 else None,
                                'observacao': row_anterior[10] if len(row_anterior) > 10 else None
                            }
                        else:
                            registro_anterior = None
                except Exception as e:
                    return Response(
                        {"error": f"Erro ao buscar registros: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            elif tabela == 'AUD_REPORT':
                # AUD_REPORT usa RECMODIFIEDON para data de modificação
                try:
                    with connection.cursor() as cursor:
                        # Busca TODOS os registros com o mesmo ID, ordenados por data DESC
                        cursor.execute("""
                            SELECT ID, CODIGO, DESCRICAO, CODAPLICACAO, 
                                   RECCREATEDBY, RECCREATEDON, RECMODIFIEDBY, RECMODIFIEDON,
                                   PRIORIDADE, OBSERVACAO
                            FROM AUD_REPORT 
                            WHERE ID = %s 
                            ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC
                        """, [registro_id])
                        
                        rows = cursor.fetchall()
                        
                        if not rows or len(rows) == 0:
                            return Response(
                                {"error": "Registro não encontrado"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                        
                        # Se data_modificacao foi fornecida, busca o registro específico
                        indice_atual = 0
                        if data_modificacao:
                            try:
                                # Converte a data de modificação para comparar
                                # Remove timezone e microsegundos se houver
                                import re
                                # Formato esperado: 2025-10-09T13:39:33.000 ou 2025-10-09 13:39:33
                                data_mod_str = data_modificacao.replace('T', ' ')
                                # Remove microsegundos e timezone
                                data_mod_str = re.sub(r'\.\d+', '', data_mod_str)  # Remove .000
                                data_mod_str = re.sub(r'[+-]\d{2}:\d{2}$', '', data_mod_str)  # Remove +00:00
                                data_mod_str = data_mod_str.strip()
                                if len(data_mod_str) > 19:
                                    data_mod_str = data_mod_str[:19]
                                data_mod = datetime.strptime(data_mod_str, '%Y-%m-%d %H:%M:%S')
                                
                                # Encontra o índice do registro com a data de modificação correspondente
                                for idx, row in enumerate(rows):
                                    recmodifiedon = row[7] if len(row) > 7 else None
                                    reccreatedon = row[5] if len(row) > 5 else None
                                    
                                    # Compara a data de modificação (ou criação se não houver modificação)
                                    data_registro = recmodifiedon if recmodifiedon else reccreatedon
                                    if data_registro:
                                        # Compara apenas data e hora (sem microsegundos)
                                        if hasattr(data_registro, 'replace'):
                                            data_registro_clean = data_registro.replace(microsecond=0)
                                        else:
                                            data_registro_clean = data_registro
                                        
                                        # Compara apenas até o segundo (sem microsegundos)
                                        if isinstance(data_registro_clean, datetime):
                                            data_registro_compare = data_registro_clean.replace(microsecond=0)
                                        else:
                                            data_registro_compare = data_registro_clean
                                        
                                        if data_registro_compare == data_mod:
                                            indice_atual = idx
                                            break
                            except (ValueError, AttributeError) as e:
                                pass
                        
                        # Registro atual = registro no índice encontrado
                        row_atual = rows[indice_atual]
                        recmodifiedby_atual = row_atual[6] if len(row_atual) > 6 and row_atual[6] else (row_atual[4] if len(row_atual) > 4 else None)
                        recmodifiedon_atual = row_atual[7] if len(row_atual) > 7 else None
                        registro_atual = {
                            'id': row_atual[0],
                            'codigo': row_atual[1] if len(row_atual) > 1 else None,
                            'descricao': row_atual[2] if len(row_atual) > 2 else None,
                            'codaplicacao': row_atual[3] if len(row_atual) > 3 else None,
                            'reccreatedby': recmodifiedby_atual,
                            'reccreatedon': row_atual[5].isoformat() if len(row_atual) > 5 and row_atual[5] and hasattr(row_atual[5], 'isoformat') else (str(row_atual[5]) if len(row_atual) > 5 and row_atual[5] else None),
                            'recmmodifiedon': recmodifiedon_atual.isoformat() if recmodifiedon_atual and hasattr(recmodifiedon_atual, 'isoformat') else (str(recmodifiedon_atual) if recmodifiedon_atual else None),
                            'prioridade': row_atual[8] if len(row_atual) > 8 else None,
                            'observacao': row_atual[9] if len(row_atual) > 9 else None
                        }
                        
                        # Registro anterior = registro imediatamente anterior ao atual (se existir)
                        if indice_atual + 1 < len(rows):
                            row_anterior = rows[indice_atual + 1]
                            recmodifiedby_anterior = row_anterior[6] if len(row_anterior) > 6 and row_anterior[6] else (row_anterior[4] if len(row_anterior) > 4 else None)
                            recmodifiedon_anterior = row_anterior[7] if len(row_anterior) > 7 else None
                            reccreatedon_anterior = row_anterior[5] if len(row_anterior) > 5 else None
                            registro_anterior = {
                                'id': row_anterior[0],
                                'codigo': row_anterior[1] if len(row_anterior) > 1 else None,
                                'descricao': row_anterior[2] if len(row_anterior) > 2 else None,
                                'codaplicacao': row_anterior[3] if len(row_anterior) > 3 else None,
                                'reccreatedby': recmodifiedby_anterior,
                                'reccreatedon': reccreatedon_anterior.isoformat() if reccreatedon_anterior and hasattr(reccreatedon_anterior, 'isoformat') else (str(reccreatedon_anterior) if reccreatedon_anterior else None),
                                'recmmodifiedon': recmodifiedon_anterior.isoformat() if recmodifiedon_anterior and hasattr(recmodifiedon_anterior, 'isoformat') else (str(recmodifiedon_anterior) if recmodifiedon_anterior else None),
                                'prioridade': row_anterior[8] if len(row_anterior) > 8 else None,
                                'observacao': row_anterior[9] if len(row_anterior) > 9 else None
                            }
                        else:
                            registro_anterior = None
                except Exception as e:
                    return Response(
                        {"error": f"Erro ao buscar registros: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            elif tabela == 'AUD_FV':
                try:
                    with connection.cursor() as cursor:
                        # Busca TODOS os registros com o mesmo ID, ordenados por data DESC
                        cursor.execute("""
                            SELECT ID, NOME, DESCRICAO, IDCATEGORIA, ATIVO, 
                                   RECCREATEDBY, RECCREATEDON, RECMODIFIEDBY, RECMODIFIEDON,
                                   PRIORIDADE, OBSERVACAO
                            FROM AUD_FV 
                            WHERE ID = %s 
                            ORDER BY COALESCE(RECMODIFIEDON, RECCREATEDON) DESC, RECCREATEDON DESC
                        """, [registro_id])
                        
                        rows = cursor.fetchall()
                        
                        if not rows or len(rows) == 0:
                            return Response(
                                {"error": "Registro não encontrado"},
                                status=status.HTTP_404_NOT_FOUND
                            )
                        
                        # Se data_modificacao foi fornecida, busca o registro específico
                        indice_atual = 0
                        if data_modificacao:
                            try:
                                # Converte a data de modificação para comparar
                                # Remove timezone e microsegundos se houver
                                import re
                                # Formato esperado: 2025-10-09T13:39:33.000 ou 2025-10-09 13:39:33
                                data_mod_str = data_modificacao.replace('T', ' ')
                                # Remove microsegundos e timezone
                                data_mod_str = re.sub(r'\.\d+', '', data_mod_str)  # Remove .000
                                data_mod_str = re.sub(r'[+-]\d{2}:\d{2}$', '', data_mod_str)  # Remove +00:00
                                data_mod_str = data_mod_str.strip()
                                if len(data_mod_str) > 19:
                                    data_mod_str = data_mod_str[:19]
                                data_mod = datetime.strptime(data_mod_str, '%Y-%m-%d %H:%M:%S')
                                
                                # Encontra o índice do registro com a data de modificação correspondente
                                for idx, row in enumerate(rows):
                                    recmodifiedon = row[8] if len(row) > 8 else None
                                    reccreatedon = row[6] if len(row) > 6 else None
                                    
                                    # Compara a data de modificação (ou criação se não houver modificação)
                                    data_registro = recmodifiedon if recmodifiedon else reccreatedon
                                    if data_registro:
                                        # Compara apenas data e hora (sem microsegundos)
                                        if hasattr(data_registro, 'replace'):
                                            data_registro_clean = data_registro.replace(microsecond=0)
                                        else:
                                            data_registro_clean = data_registro
                                        
                                        # Compara apenas até o segundo (sem microsegundos)
                                        if isinstance(data_registro_clean, datetime):
                                            data_registro_compare = data_registro_clean.replace(microsecond=0)
                                        else:
                                            data_registro_compare = data_registro_clean
                                        
                                        if data_registro_compare == data_mod:
                                            indice_atual = idx
                                            break
                            except (ValueError, AttributeError) as e:
                                pass
                        
                        # Registro atual = registro no índice encontrado
                        row_atual = rows[indice_atual]
                        recmodifiedby_atual = row_atual[7] if len(row_atual) > 7 and row_atual[7] else (row_atual[5] if len(row_atual) > 5 else None)
                        recmodifiedon_atual = row_atual[8] if len(row_atual) > 8 else None
                        registro_atual = {
                            'id': row_atual[0],
                            'nome': row_atual[1] if len(row_atual) > 1 else None,
                            'descricao': row_atual[2] if len(row_atual) > 2 else None,
                            'idcategoria': row_atual[3] if len(row_atual) > 3 else None,
                            'ativo': row_atual[4] if len(row_atual) > 4 else None,
                            'reccreatedby': recmodifiedby_atual,
                            'reccreatedon': row_atual[6].isoformat() if len(row_atual) > 6 and row_atual[6] and hasattr(row_atual[6], 'isoformat') else (str(row_atual[6]) if len(row_atual) > 6 and row_atual[6] else None),
                            'recmmodifiedon': recmodifiedon_atual.isoformat() if recmodifiedon_atual and hasattr(recmodifiedon_atual, 'isoformat') else (str(recmodifiedon_atual) if recmodifiedon_atual else None),
                            'prioridade': row_atual[9] if len(row_atual) > 9 else None,
                            'observacao': row_atual[10] if len(row_atual) > 10 else None
                        }
                        
                        # Registro anterior = registro imediatamente anterior ao atual (se existir)
                        if indice_atual + 1 < len(rows):
                            row_anterior = rows[indice_atual + 1]
                            recmodifiedby_anterior = row_anterior[7] if len(row_anterior) > 7 and row_anterior[7] else (row_anterior[5] if len(row_anterior) > 5 else None)
                            recmodifiedon_anterior = row_anterior[8] if len(row_anterior) > 8 else None
                            reccreatedon_anterior = row_anterior[6] if len(row_anterior) > 6 else None
                            registro_anterior = {
                                'id': row_anterior[0],
                                'nome': row_anterior[1] if len(row_anterior) > 1 else None,
                                'descricao': row_anterior[2] if len(row_anterior) > 2 else None,
                                'idcategoria': row_anterior[3] if len(row_anterior) > 3 else None,
                                'ativo': row_anterior[4] if len(row_anterior) > 4 else None,
                                'reccreatedby': recmodifiedby_anterior,
                                'reccreatedon': reccreatedon_anterior.isoformat() if reccreatedon_anterior and hasattr(reccreatedon_anterior, 'isoformat') else (str(reccreatedon_anterior) if reccreatedon_anterior else None),
                                'recmmodifiedon': recmodifiedon_anterior.isoformat() if recmodifiedon_anterior and hasattr(recmodifiedon_anterior, 'isoformat') else (str(recmodifiedon_anterior) if recmodifiedon_anterior else None),
                                'prioridade': row_anterior[9] if len(row_anterior) > 9 else None,
                                'observacao': row_anterior[10] if len(row_anterior) > 10 else None
                            }
                        else:
                            registro_anterior = None
                except Exception as e:
                    return Response(
                        {"error": f"Erro ao buscar registros: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                return Response(
                    {"error": "Tabela inválida. Use: AUD_SQL, AUD_REPORT ou AUD_FV"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response({
                'tabela': tabela,
                'registro_atual': registro_atual,
                'registro_anterior': registro_anterior
            })
            
        except Exception as e:
            return Response(
                {"error": f"Erro ao buscar registros: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificacoesView(APIView):
    """
    Consolida registros das tabelas AUD como notificações.
    Cada registro expõe título, descrição, prioridade, data e status de leitura.
    """

    DEFAULT_LIMIT = 120
    MAX_LIMIT = 300

    TIPO_MAP = {
        'sql': {
            'tabela': 'AUD_SQL',
            'id_field': 'codsentenca',
            'label': 'SQL'
        },
        'report': {
            'tabela': 'AUD_REPORT',
            'id_field': 'id',
            'label': 'REPORT'
        },
        'fv': {
            'tabela': 'AUD_FV',
            'id_field': 'id',
            'label': 'FV'
        }
    }

    def get(self, request):
        limit = self._sanitize_limit(request.query_params.get('limit'))
        somente_nao_lidas = request.query_params.get('somente_nao_lidas', 'false').lower() == 'true'

        notificacoes = []
        notificacoes.extend(self._build_from_queryset(CustomizacaoSQL, 'sql', somente_nao_lidas))
        notificacoes.extend(self._build_from_queryset(CustomizacaoReport, 'report', somente_nao_lidas))
        notificacoes.extend(self._build_from_queryset(CustomizacaoFV, 'fv', somente_nao_lidas))

        notificacoes.sort(key=lambda n: n['ordenacao'], reverse=True)

        # Remove campo interno de ordenação e aplica o limite global
        resposta = []
        for notif in notificacoes[:limit]:
            notif.pop('ordenacao', None)
            resposta.append(notif)

        return Response(resposta)

    def _sanitize_limit(self, raw_limit):
        try:
            parsed = int(raw_limit)
        except (TypeError, ValueError):
            return self.DEFAULT_LIMIT
        return max(1, min(parsed, self.MAX_LIMIT))

    def _build_from_queryset(self, model, tipo, somente_nao_lidas):
        config = self.TIPO_MAP[tipo]
        queryset = model.objects.annotate(
            data_ref=Coalesce('recmodifiedon', 'reccreatedon')
        ).order_by('-data_ref')[:self.MAX_LIMIT]

        notif_list = []
        for registro in queryset:
            lida = bool(getattr(registro, 'lida', 0))
            if somente_nao_lidas and lida:
                continue
            notif = self._serialize_registro(registro, tipo, config)
            notif_list.append(notif)
        return notif_list

    def _serialize_registro(self, registro, tipo, config):
        registro_id = getattr(registro, config['id_field'])
        tabela = config['tabela']
        titulo, descricao = self._resolver_titulo_descricao(registro, tipo, registro_id, config)
        prioridade = self._normalizar_prioridade(getattr(registro, 'prioridade', None))
        data_base = getattr(registro, 'data_ref', None) or getattr(registro, 'recmodifiedon', None) or getattr(registro, 'reccreatedon', None) or timezone.now()
        if timezone.is_naive(data_base):
            data_base = timezone.make_aware(data_base, timezone.get_default_timezone())

        responsavel = getattr(registro, 'recmodifiedby', None) or getattr(registro, 'reccreatedby', None) or 'Sistema'

        return {
            'id': f"{tipo}-{registro_id}",
            'registro_id': registro_id,
            'tabela': tabela,
            'titulo': titulo,
            'descricao': descricao,
            'prioridade': prioridade,
            'lida': bool(getattr(registro, 'lida', 0)),
            'data_hora': data_base.isoformat(),
            'responsavel': responsavel,
            'origem': config['label'],
            'ordenacao': data_base.timestamp()
        }

    def _resolver_titulo_descricao(self, registro, tipo, registro_id, config):
        # Determina se foi criação ou modificação
        foi_modificado = getattr(registro, 'recmodifiedon', None) is not None
        acao = "modificado" if foi_modificado else "criado"
        
        if tipo == 'sql':
            nome_registro = registro.titulo or f"SQL {registro_id}"
            titulo = f"Alteração em {config['label']}: {nome_registro}"
            descricao = f"Registro {acao} na tabela {config['tabela']}"
            if registro.observacao:
                descricao += f" - {self._truncate(registro.observacao, 100)}"
        elif tipo == 'report':
            nome_registro = registro.codigo or f"Report {registro_id}"
            titulo = f"Alteração em {config['label']}: {nome_registro}"
            descricao = f"Registro {acao} na tabela {config['tabela']}"
            if registro.observacao:
                descricao += f" - {self._truncate(registro.observacao, 100)}"
        else:  # fv
            nome_registro = registro.nome or f"FV {registro_id}"
            titulo = f"Alteração em {config['label']}: {nome_registro}"
            descricao = f"Registro {acao} na tabela {config['tabela']}"
            if registro.observacao:
                descricao += f" - {self._truncate(registro.observacao, 100)}"
        return titulo, descricao

    def _truncate(self, texto, limite=280):
        if not texto:
            return 'Sem descrição disponível.'
        texto = str(texto).strip()
        if len(texto) <= limite:
            return texto
        return f"{texto[:limite-3]}..."

    def _normalizar_prioridade(self, valor):
        if not valor:
            return 'Baixa'
        valor = str(valor).strip().capitalize()
        if valor.lower() in ['alta', 'média', 'media', 'baixa']:
            if valor.lower() == 'media':
                return 'Média'
            return valor
        return 'Baixa'


class MarcarNotificacaoLidaView(APIView):
    """
    Atualiza o campo 'lida' diretamente nas tabelas AUD de origem.
    Recebe o identificador composto (ex.: sql-123) via URL.
    """

    def post(self, request, uid):
        tipo, registro_id = self._parse_uid(uid)
        if not tipo:
            return Response(
                {"error": "Identificador inválido. Use o formato <tipo>-<id>."},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_info = NotificacoesView.TIPO_MAP.get(tipo)
        if not model_info:
            return Response(
                {"error": f"Tipo '{tipo}' não suportado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        model = self._resolver_modelo(tipo)
        lookup_field = model_info['id_field']
        filtro = {lookup_field: registro_id}

        registro = model.objects.filter(**filtro).first()
        if not registro:
            return Response(
                {"error": f"Registro {registro_id} não encontrado em {model_info['tabela']}."},
                status=status.HTTP_404_NOT_FOUND
            )

        registro.lida = 1
        registro.save(update_fields=['lida'])

        return Response({
            "success": True,
            "uid": uid,
            "registro_id": registro_id,
            "tabela": model_info['tabela']
        })

    def _parse_uid(self, uid):
        if not uid or '-' not in uid:
            return None, None
        tipo, registro_id = uid.split('-', 1)
        tipo = tipo.lower()
        try:
            registro_id = int(registro_id)
        except ValueError:
            return None, None
        return tipo, registro_id

    def _resolver_modelo(self, tipo):
        if tipo == 'sql':
            return CustomizacaoSQL
        if tipo == 'report':
            return CustomizacaoReport
        return CustomizacaoFV