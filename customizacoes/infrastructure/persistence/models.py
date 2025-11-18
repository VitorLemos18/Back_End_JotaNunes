"""
Django models moved to infrastructure/persistence layer.
This file imports from the original models.py to maintain compatibility.
"""
# Import all models from the original location
from ...models import (
    CustomizacaoFV,
    CustomizacaoSQL,
    CustomizacaoReport,
    Prioridade,
    Observacao,
    CadastroDependencias,
    Notificacao
)

__all__ = [
    'CustomizacaoFV',
    'CustomizacaoSQL',
    'CustomizacaoReport',
    'Prioridade',
    'Observacao',
    'CadastroDependencias',
    'Notificacao'
]





