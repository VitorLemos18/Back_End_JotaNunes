"""
Infrastructure implementation of IAudSQLRepository using Django ORM.
"""
from typing import List, Optional, Dict, Any
from django.db import connection
from ...domain.repositories.aud_repository import IAudSQLRepository
from ...infrastructure.persistence.models import CustomizacaoSQL


class DjangoAudSQLRepository(IAudSQLRepository):
    """Django implementation of AUD_SQL repository."""
    
    def get_by_id(self, codsentenca: str) -> Optional[Dict[str, Any]]:
        """Get the most recent record by CODSENTENCA."""
        records = self.get_all_by_id(codsentenca)
        return records[0] if records else None
    
    def get_all_by_id(self, codsentenca: str) -> List[Dict[str, Any]]:
        """Get all records with the same CODSENTENCA, ordered by date DESC."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT CODSENTENCA, TITULO, SENTENCA, APLICACAO, TAMANHO, 
                       RECCREATEDBY, RECCREATEDON, RECMODIFIEDBY
                FROM AUD_SQL 
                WHERE CODSENTENCA = %s 
                ORDER BY RECCREATEDON DESC
            """, [codsentenca])
            
            rows = cursor.fetchall()
            result = []
            
            for row in rows:
                reccreatedby = row[7] if len(row) > 7 and row[7] else (row[5] if len(row) > 5 else None)
                result.append({
                    'codsentenca': row[0],
                    'titulo': row[1] if len(row) > 1 else None,
                    'sentenca': row[2] if len(row) > 2 else None,
                    'aplicacao': row[3] if len(row) > 3 else None,
                    'tamanho': row[4] if len(row) > 4 else None,
                    'reccreatedby': reccreatedby,
                    'reccreatedon': row[6] if len(row) > 6 else None
                })
            
            return result
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all records."""
        records = CustomizacaoSQL.objects.all().order_by('-reccreatedon')
        result = []
        
        for reg in records:
            # Try to get RECMODIFIEDBY
            reccreatedby = reg.reccreatedby or 'N/A'
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT RECMODIFIEDBY FROM AUD_SQL WHERE CODSENTENCA = %s", [reg.codsentenca])
                    row = cursor.fetchone()
                    if row and row[0]:
                        reccreatedby = row[0]
            except:
                pass
            
            result.append({
                'codsentenca': reg.codsentenca,
                'titulo': reg.titulo,
                'sentenca': reg.sentenca,
                'aplicacao': reg.aplicacao,
                'tamanho': reg.tamanho,
                'reccreatedby': reccreatedby,
                'reccreatedon': reg.reccreatedon
            })
        
        return result





