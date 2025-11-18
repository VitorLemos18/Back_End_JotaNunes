# customizacoes/serializers.py

from rest_framework import serializers
from .models import (
    CustomizacaoFV, CustomizacaoSQL, CustomizacaoReport,
    CadastroDependencias
)


class CustomizacaoFVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizacaoFV
        fields = '__all__'


class CustomizacaoSQLSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizacaoSQL
        fields = '__all__'


class CustomizacaoReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizacaoReport
        fields = '__all__'


class CadastroDependenciasSerializer(serializers.ModelSerializer):
    origem_label = serializers.SerializerMethodField()
    destino_label = serializers.SerializerMethodField()
    origem_id = serializers.SerializerMethodField()
    origem_nome = serializers.SerializerMethodField()
    origem_tabela = serializers.SerializerMethodField()
    destino_id = serializers.SerializerMethodField()
    destino_nome = serializers.SerializerMethodField()
    destino_tabela = serializers.SerializerMethodField()
    prioridade_nivel = serializers.SerializerMethodField()
    criado_por_nome = serializers.SerializerMethodField()

    class Meta:
        model = CadastroDependencias
        fields = '__all__'
        read_only_fields = ['data_criacao', 'criado_por']

    def get_origem_label(self, obj):
        return obj.get_origem_display()

    def get_destino_label(self, obj):
        return obj.get_destino_display()

    def _determinar_origem_destino(self, obj):
        """Determina qual campo é origem e qual é destino baseado na lógica do modelo"""
        # A lógica do modelo: se id_aud_sql está preenchido E (id_aud_report OU id_aud_fv está preenchido),
        # então id_aud_sql é a origem
        # Similar para os outros casos
        
        origem_tipo = None
        destino_tipo = None
        
        if obj.id_aud_sql and obj.id_aud_report:
            origem_tipo = 'sql'
            destino_tipo = 'report'
        elif obj.id_aud_sql and obj.id_aud_fv:
            origem_tipo = 'sql'
            destino_tipo = 'fv'
        elif obj.id_aud_report and obj.id_aud_sql:
            origem_tipo = 'report'
            destino_tipo = 'sql'
        elif obj.id_aud_report and obj.id_aud_fv:
            origem_tipo = 'report'
            destino_tipo = 'fv'
        elif obj.id_aud_fv and obj.id_aud_sql:
            origem_tipo = 'fv'
            destino_tipo = 'sql'
        elif obj.id_aud_fv and obj.id_aud_report:
            origem_tipo = 'fv'
            destino_tipo = 'report'
        
        return origem_tipo, destino_tipo

    def get_origem_tabela(self, obj):
        """Retorna o nome da tabela de origem"""
        origem_tipo, _ = self._determinar_origem_destino(obj)
        if origem_tipo == 'sql':
            return 'AUD_SQL'
        elif origem_tipo == 'report':
            return 'AUD_Report'
        elif origem_tipo == 'fv':
            return 'AUD_FV'
        return None

    def get_origem_id(self, obj):
        """Retorna o ID da origem"""
        origem_tipo, _ = self._determinar_origem_destino(obj)
        if origem_tipo == 'sql':
            return obj.id_aud_sql
        elif origem_tipo == 'report':
            return obj.id_aud_report
        elif origem_tipo == 'fv':
            return obj.id_aud_fv
        return None

    def get_origem_nome(self, obj):
        """Retorna o nome da origem baseado no tipo"""
        origem_tipo, _ = self._determinar_origem_destino(obj)
        try:
            if origem_tipo == 'sql' and obj.id_aud_sql:
                sql = CustomizacaoSQL.objects.get(codsentenca=obj.id_aud_sql)
                return sql.titulo or sql.codsentenca
            elif origem_tipo == 'report' and obj.id_aud_report:
                report = CustomizacaoReport.objects.get(id=obj.id_aud_report)
                return report.codigo or obj.id_aud_report
            elif origem_tipo == 'fv' and obj.id_aud_fv:
                fv = CustomizacaoFV.objects.get(id=obj.id_aud_fv)
                return fv.nome or str(obj.id_aud_fv)
        except Exception as e:
            pass
        return None

    def get_destino_tabela(self, obj):
        """Retorna o nome da tabela de destino"""
        _, destino_tipo = self._determinar_origem_destino(obj)
        if destino_tipo == 'sql':
            return 'AUD_SQL'
        elif destino_tipo == 'report':
            return 'AUD_Report'
        elif destino_tipo == 'fv':
            return 'AUD_FV'
        return None

    def get_destino_id(self, obj):
        """Retorna o ID do destino"""
        _, destino_tipo = self._determinar_origem_destino(obj)
        if destino_tipo == 'sql':
            return obj.id_aud_sql
        elif destino_tipo == 'report':
            return obj.id_aud_report
        elif destino_tipo == 'fv':
            return obj.id_aud_fv
        return None

    def get_destino_nome(self, obj):
        """Retorna o nome do destino baseado no tipo"""
        _, destino_tipo = self._determinar_origem_destino(obj)
        try:
            if destino_tipo == 'sql' and obj.id_aud_sql:
                sql = CustomizacaoSQL.objects.get(codsentenca=obj.id_aud_sql)
                return sql.titulo or sql.codsentenca
            elif destino_tipo == 'report' and obj.id_aud_report:
                report = CustomizacaoReport.objects.get(id=obj.id_aud_report)
                return report.codigo or obj.id_aud_report
            elif destino_tipo == 'fv' and obj.id_aud_fv:
                fv = CustomizacaoFV.objects.get(id=obj.id_aud_fv)
                return fv.nome or str(obj.id_aud_fv)
        except Exception as e:
            pass
        return None

    def get_prioridade_nivel(self, obj):
        """Retorna a prioridade do registro de origem (ou destino se origem não tiver)"""
        origem_tipo, destino_tipo = self._determinar_origem_destino(obj)
        
        # Tenta buscar a prioridade da origem primeiro
        try:
            if origem_tipo == 'sql' and obj.id_aud_sql:
                sql = CustomizacaoSQL.objects.get(codsentenca=obj.id_aud_sql)
                if sql.prioridade:
                    return sql.prioridade
            elif origem_tipo == 'report' and obj.id_aud_report:
                report = CustomizacaoReport.objects.get(id=obj.id_aud_report)
                if report.prioridade:
                    return report.prioridade
            elif origem_tipo == 'fv' and obj.id_aud_fv:
                fv = CustomizacaoFV.objects.get(id=obj.id_aud_fv)
                if fv.prioridade:
                    return fv.prioridade
        except Exception:
            pass
        
        # Se origem não tiver prioridade, tenta buscar do destino
        # Usa o campo correto do destino (que é diferente do campo da origem)
        try:
            if destino_tipo == 'sql' and obj.id_aud_sql:
                # Se destino é SQL, usa o campo id_aud_sql (mas só se origem não for SQL)
                if origem_tipo != 'sql':  # Garante que não está usando o mesmo campo da origem
                    sql = CustomizacaoSQL.objects.get(codsentenca=obj.id_aud_sql)
                    if sql.prioridade:
                        return sql.prioridade
            elif destino_tipo == 'report' and obj.id_aud_report:
                # Se destino é Report, usa o campo id_aud_report (mas só se origem não for Report)
                if origem_tipo != 'report':
                    report = CustomizacaoReport.objects.get(id=obj.id_aud_report)
                    if report.prioridade:
                        return report.prioridade
            elif destino_tipo == 'fv' and obj.id_aud_fv:
                # Se destino é FV, usa o campo id_aud_fv (mas só se origem não for FV)
                if origem_tipo != 'fv':
                    fv = CustomizacaoFV.objects.get(id=obj.id_aud_fv)
                    if fv.prioridade:
                        return fv.prioridade
        except Exception:
            pass
        
        return None

    def get_criado_por_nome(self, obj):
        """Retorna o nome do usuário que criou a dependência"""
        if obj.criado_por:
            try:
                from .models import Usuario
                usuario = Usuario.objects.get(id_usuario=obj.criado_por)
                return usuario.nome
            except:
                return None
        return None

    def validate(self, data):
        sql = data.get('id_aud_sql')
        rep = data.get('id_aud_report')
        fv = data.get('id_aud_fv')
        preenchidos = sum(1 for x in [sql, rep, fv] if x is not None)

        if preenchidos != 2:
            raise serializers.ValidationError("Exatamente 2 campos devem ser preenchidos.")

        tipos = []
        if sql: tipos.append('sql')
        if rep: tipos.append('report')
        if fv: tipos.append('fv')
        if len(set(tipos)) != 2:
            raise serializers.ValidationError("Origem e destino devem ser de tipos diferentes.")

        return data

    def create(self, validated_data):
        # Se houver um usuário no contexto da requisição, usar o ID
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            # Assumindo que o user tem um id_usuario ou podemos usar o id do User do Django
            validated_data['criado_por'] = getattr(request.user, 'id', None)
        return super().create(validated_data)