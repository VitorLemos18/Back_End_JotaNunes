# customizacoes/tasks.py
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .models import CustomizacaoFV
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

@shared_task
def enviar_relatorio_fv(destinatario):
    fvs = CustomizacaoFV.objects.filter(ativo=True)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Relatório de Fórmulas Visuais Ativas", styles['Title']))
    elements.append(Paragraph(f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}", styles['Normal']))

    data = [['ID', 'Nome', 'Categoria', 'Ativo']]
    for fv in fvs:
        data.append([fv.aud_id, fv.nome or '-', fv.idcategoria, 'Sim' if fv.ativo else 'Não'])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)

    email = EmailMessage(
        'Relatório de FVs Ativas',
        f"Total: {fvs.count()} FVs ativas.",
        settings.DEFAULT_FROM_EMAIL,
        [destinatario]
    )
    email.attach('fvs_ativas.pdf', buffer.getvalue(), 'application/pdf')
    email.send()
    buffer.close()