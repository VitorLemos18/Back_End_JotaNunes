# customizacoes/management/commands/import_aud.py
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from customizacoes.models import CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport


def parse_int(value):
    """Converte string para int, retorna None se vazio ou inválido"""
    if not value or value.strip() == '':
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_codaplicacao(value):
    """Converte CODAPLICACAO (pode ser letra como 'M', 'G', 'X' ou número) para int"""
    if not value or value.strip() == '':
        return None
    
    value = str(value).strip().upper()
    
    # Tenta converter diretamente para int
    try:
        return int(value)
    except ValueError:
        pass
    
    # Se for uma letra, converte para código ASCII ou mapeamento conhecido
    if len(value) == 1 and value.isalpha():
        # Usa o código ASCII da letra como valor numérico
        return ord(value)
    
    # Se não conseguir, retorna None
    return None


def parse_bool(value):
    """Converte string para bool"""
    if not value or value.strip() == '':
        return True  # Default True para ATIVO
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().upper() in ('1', 'TRUE', 'SIM', 'S', 'Y', 'YES')


def parse_datetime_field(value):
    """Converte string para datetime, retorna None se vazio ou inválido"""
    if not value or value.strip() == '':
        return None
    try:
        # Tenta vários formatos comuns
        dt = parse_datetime(value)
        if dt:
            return dt
        # Tenta formato com milissegundos
        for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = 'Importa CSV para tabelas AUD_ (permite importação parcial de dados)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Caminho do arquivo CSV')
        parser.add_argument('model', choices=['fv', 'sql', 'report'], help='Tipo de modelo a importar')
        parser.add_argument(
            '--update',
            action='store_true',
            help='Atualiza registros existentes ao invés de apenas criar novos'
        )

    def handle(self, *args, **options):
        path = options['csv_file']
        model_type = options['model']
        update_existing = options['update']

        imported = 0
        updated = 0
        errors = []

        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):  # Começa em 2 (linha 1 é header)
                    try:
                        if model_type == 'fv':
                            result = self._import_fv(row, update_existing)
                        elif model_type == 'sql':
                            result = self._import_sql(row, update_existing)
                        elif model_type == 'report':
                            result = self._import_report(row, update_existing)
                        
                        if result == 'created':
                            imported += 1
                        elif result == 'updated':
                            updated += 1
                            
                    except Exception as e:
                        errors.append(f"Linha {row_num}: {str(e)}")
                        self.stdout.write(self.style.WARNING(f"Erro na linha {row_num}: {str(e)}"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Arquivo não encontrado: {path}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao ler arquivo: {str(e)}'))
            return

        # Resumo
        self.stdout.write(self.style.SUCCESS(
            f'\nImportação concluída:\n'
            f'  - {imported} registros criados\n'
            f'  - {updated} registros atualizados\n'
            f'  - {len(errors)} erros'
        ))

    def _import_fv(self, row, update_existing):
        """Importa registro AUD_FV"""
        # Mapeia campos do CSV para o modelo
        data = {
            'id': parse_int(row.get('ID')),
            'codcoligada': parse_int(row.get('CODCOLIGADA')),
            'nome': row.get('NOME', '').strip() or None,
            'descricao': row.get('DESCRICAO', '').strip() or None,
            'idcategoria': parse_int(row.get('IDCATEGORIA')),
            'ativo': parse_bool(row.get('ATIVO', '1')),
            'reccreatedby': row.get('RECCREATEDBY', '').strip() or None,
            'reccreatedon': parse_datetime_field(row.get('RECCREATEDON')),
            'recmodifiedby': row.get('RECMODIFIEDBY', '').strip() or None,
            'recmodifiedon': parse_datetime_field(row.get('RECMODIFIEDON')),
        }

        if not data['id']:
            raise ValueError("Campo ID é obrigatório")

        if update_existing:
            obj, created = CustomizacaoFV.objects.update_or_create(
                id=data['id'],
                defaults={k: v for k, v in data.items() if k != 'id'}
            )
            return 'created' if created else 'updated'
        else:
            CustomizacaoFV.objects.get_or_create(
                id=data['id'],
                defaults={k: v for k, v in data.items() if k != 'id'}
            )
            return 'created'

    def _import_sql(self, row, update_existing):
        """Importa registro AUD_SQL"""
        # Mapeia campos do CSV para o modelo
        # Nota: CODSENTENCA no CSV pode ser string (ex: "CODEF001.0005"), 
        # mas o modelo espera IntegerField. Vamos tentar converter.
        codsentenca_str = row.get('CODSENTENCA', '').strip()
        if not codsentenca_str:
            raise ValueError("Campo CODSENTENCA é obrigatório")
        
        # Tenta converter para int
        codsentenca = None
        try:
            # Tenta conversão direta
            codsentenca = int(codsentenca_str)
        except ValueError:
            # Se não for numérico, tenta extrair números do início ou fim
            import re
            # Remove pontos e tenta converter
            cleaned = codsentenca_str.replace('.', '').replace('-', '').replace('_', '')
            numbers = re.findall(r'\d+', cleaned)
            if numbers:
                # Usa o primeiro número encontrado
                try:
                    codsentenca = int(numbers[0])
                except (ValueError, IndexError):
                    pass
            
            # Se ainda não conseguiu, gera um hash do string como fallback
            # AVISO: Isso pode causar colisões, mas permite importar dados com CODSENTENCA não numérico
            if codsentenca is None:
                # Gera um hash positivo do string
                hash_value = abs(hash(codsentenca_str)) % (10 ** 9)  # Limita a 9 dígitos
                self.stdout.write(
                    self.style.WARNING(
                        f"CODSENTENCA '{codsentenca_str}' não é numérico. "
                        f"Usando hash: {hash_value}. "
                        f"Considere ajustar o modelo para CharField se necessário."
                    )
                )
                codsentenca = hash_value

        data = {
            'codcoligada': parse_int(row.get('CODCOLIGADA')),
            'aplicacao': row.get('APLICACAO', '').strip() or None,
            'titulo': row.get('TITULO', '').strip() or None,
            'sentenca': row.get('SENTENCA', '').strip() or None,
            'tamanho': parse_int(row.get('TAMANHO')),
            'reccreatedby': row.get('RECCREATEDBY', '').strip() or None,
            'reccreatedon': parse_datetime_field(row.get('RECCREATEDON')),
            'recmodifiedby': row.get('RECMODIFIEDBY', '').strip() or None,
            'recmodifiedon': parse_datetime_field(row.get('RECMODIFIEDON')),
        }

        if update_existing:
            obj, created = CustomizacaoSQL.objects.update_or_create(
                codsentenca=codsentenca,
                defaults=data
            )
            return 'created' if created else 'updated'
        else:
            CustomizacaoSQL.objects.get_or_create(
                codsentenca=codsentenca,
                defaults=data
            )
            return 'created'

    def _import_report(self, row, update_existing):
        """Importa registro AUD_REPORT"""
        # Mapeia campos do CSV para o modelo
        data = {
            'id': parse_int(row.get('ID')),
            'codcoligada': parse_int(row.get('CODCOLIGADA')),
            'codaplicacao': parse_codaplicacao(row.get('CODAPLICACAO')),  # Pode ser letra ou número
            'codigo': row.get('CODIGO', '').strip() or None,
            'descricao': row.get('DESCRICAO', '').strip() or None,
            'reccreatedby': row.get('RECCREATEDBY', '').strip() or None,
            'reccreatedon': parse_datetime_field(row.get('RECCREATEDON')),
            'recmodifiedby': row.get('USRULTALTERACAO', '').strip() or None,  # CSV usa USRULTALTERACAO
            'recmodifiedon': parse_datetime_field(row.get('DATAULTALTERACAO')),  # CSV usa DATAULTALTERACAO
        }

        if not data['id']:
            raise ValueError("Campo ID é obrigatório")

        if update_existing:
            obj, created = CustomizacaoReport.objects.update_or_create(
                id=data['id'],
                defaults={k: v for k, v in data.items() if k != 'id'}
            )
            return 'created' if created else 'updated'
        else:
            CustomizacaoReport.objects.get_or_create(
                id=data['id'],
                defaults={k: v for k, v in data.items() if k != 'id'}
            )
            return 'created'