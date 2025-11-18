# customizacoes/urls.py
"""
URL configuration for customizacoes app.
Organized by functionality following RESTful principles.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # ViewSets (CRUD operations)
    CustomizacaoFVViewSet,
    CustomizacaoSQLViewSet,
    CustomizacaoReportViewSet,
    # PrioridadeViewSet,  # REMOVIDO - tabela não existe mais
    # ObservacaoViewSet,  # REMOVIDO - tabela não existe mais
    # NotificacaoViewSet,  # REMOVIDO - tabela não existe mais
    CadastroDependenciasViewSet,
    # API Views (Custom endpoints)
    InsightsFVView,
    InsightsSQLView,
    InsightsReportView,
    InsightsDependenciasView,
    InsightsPrioridadesView,
    RegistrosModalView,
    HistoricoAlteracoesView,
    AdicionarObservacaoRegistroView,
    CompararRegistrosView,
)

# ============================================================================
# ROUTER - ViewSets (RESTful CRUD operations)
# ============================================================================
router = DefaultRouter()

# AUD Tables (Read-only)
router.register(r'fv', CustomizacaoFVViewSet, basename='fv')
router.register(r'sql', CustomizacaoSQLViewSet, basename='sql')
router.register(r'reports', CustomizacaoReportViewSet, basename='reports')

# Management Tables (Full CRUD)
# router.register(r'prioridades', PrioridadeViewSet, basename='prioridades')  # REMOVIDO
# router.register(r'observacoes', ObservacaoViewSet, basename='observacoes')  # REMOVIDO
# router.register(r'notificacoes', NotificacaoViewSet, basename='notificacoes')  # REMOVIDO
router.register(r'dependencias', CadastroDependenciasViewSet, basename='dependencias')

# ============================================================================
# URL PATTERNS - Custom API endpoints
# ============================================================================
urlpatterns = [
    # Router URLs (ViewSets)
    path('', include(router.urls)),
    
    # ========================================================================
    # INSIGHTS - Analytics and statistics
    # ========================================================================
    path('insights/fv', InsightsFVView.as_view(), name='insights-fv'),
    path('insights/sql', InsightsSQLView.as_view(), name='insights-sql'),
    path('insights/report', InsightsReportView.as_view(), name='insights-report'),
    path('insights/dependencias', InsightsDependenciasView.as_view(), name='insights-dependencias'),
    path('insights/prioridades', InsightsPrioridadesView.as_view(), name='insights-prioridades'),
    
    # ========================================================================
    # MODAL & REGISTROS - Modal data and record operations
    # ========================================================================
    path('registros-modal/', RegistrosModalView.as_view(), name='registros-modal'),
    
    # ========================================================================
    # HISTÓRICO - History and comparison operations
    # ========================================================================
    path('historico-alteracoes/', HistoricoAlteracoesView.as_view(), name='historico-alteracoes'),
    path('comparar-registros/', CompararRegistrosView.as_view(), name='comparar-registros'),
    
    # ========================================================================
    # OBSERVAÇÕES - Observation operations
    # ========================================================================
    path('adicionar-observacao-registro/', AdicionarObservacaoRegistroView.as_view(), name='adicionar-observacao-registro'),
]
