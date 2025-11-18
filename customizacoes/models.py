# customizacoes/models.py
from django.db import models
from django.core.exceptions import ValidationError

# === TABELAS AUD (GERENCIADAS) ===
class CustomizacaoFV(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    codcoligada = models.IntegerField(db_column='CODCOLIGADA', null=True, blank=True)
    nome = models.CharField(max_length=255, db_column='NOME', blank=True, null=True)
    descricao = models.TextField(db_column='DESCRICAO', blank=True, null=True)
    idcategoria = models.IntegerField(db_column='IDCATEGORIA', null=True, blank=True)
    ativo = models.BooleanField(db_column='ATIVO', default=True)
    prioridade = models.CharField(max_length=50, db_column='PRIORIDADE', blank=True, null=True)
    observacao = models.TextField(db_column='OBSERVACAO', blank=True, null=True)
    lida = models.IntegerField(db_column='LIDA', default=0)
    reccreatedby = models.CharField(max_length=100, db_column='RECCREATEDBY', blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column='RECCREATEDON', null=True, blank=True)
    recmodifiedby = models.CharField(max_length=100, db_column='RECMODIFIEDBY', blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column='RECMODIFIEDON', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'AUD_FV'

    def __str__(self):
        return f"FV {self.id}: {self.nome or 'Sem nome'}"


class CustomizacaoSQL(models.Model):
    codsentenca = models.IntegerField(primary_key=True, db_column='CODSENTENCA')
    codcoligada = models.IntegerField(db_column='CODCOLIGADA', null=True, blank=True)
    aplicacao = models.CharField(max_length=100, db_column='APLICACAO', blank=True, null=True)
    titulo = models.CharField(max_length=255, db_column='TITULO', blank=True, null=True)
    sentenca = models.TextField(db_column='SENTENCA', blank=True, null=True)
    tamanho = models.IntegerField(db_column='TAMANHO', null=True, blank=True)
    prioridade = models.CharField(max_length=50, db_column='PRIORIDADE', blank=True, null=True)
    observacao = models.TextField(db_column='OBSERVACAO', blank=True, null=True)
    lida = models.IntegerField(db_column='LIDA', default=0)
    reccreatedby = models.CharField(max_length=100, db_column='RECCREATEDBY', blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column='RECCREATEDON', null=True, blank=True)
    recmodifiedby = models.CharField(max_length=100, db_column='RECMODIFIEDBY', blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column='RECMODIFIEDON', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'AUD_SQL'

    def __str__(self):
        return f"SQL {self.codsentenca}: {self.titulo or 'Sem título'}"


class CustomizacaoReport(models.Model):
    id = models.IntegerField(primary_key=True, db_column='ID')
    codcoligada = models.IntegerField(db_column='CODCOLIGADA', null=True, blank=True)
    codaplicacao = models.IntegerField(db_column='CODAPLICACAO', null=True, blank=True)
    codigo = models.CharField(max_length=100, db_column='CODIGO', blank=True, null=True)
    descricao = models.TextField(db_column='DESCRICAO', blank=True, null=True)
    prioridade = models.CharField(max_length=50, db_column='PRIORIDADE', blank=True, null=True)
    observacao = models.TextField(db_column='OBSERVACAO', blank=True, null=True)
    lida = models.IntegerField(db_column='LIDA', default=0)
    reccreatedby = models.CharField(max_length=100, db_column='RECCREATEDBY', blank=True, null=True)
    reccreatedon = models.DateTimeField(db_column='RECCREATEDON', null=True, blank=True)
    recmodifiedby = models.CharField(max_length=100, db_column='RECMODIFIEDBY', blank=True, null=True)
    recmodifiedon = models.DateTimeField(db_column='RECMODIFIEDON', null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'AUD_REPORT'

    def __str__(self):
        return f"REP {self.id}: {self.codigo or 'Sem código'}"


# === TABELAS NOVAS (GERENCIADAS) ===
class Usuario(models.Model):
    id_usuario = models.IntegerField(primary_key=True, db_column='ID_USUARIO')
    nome = models.CharField(max_length=255, db_column='NOME')
    email = models.CharField(max_length=255, db_column='EMAIL')
    cargo = models.CharField(max_length=255, db_column='CARGO', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'USUARIO'

    def __str__(self):
        return f"{self.nome} ({self.email})"


class CadastroDependencias(models.Model):
    id = models.AutoField(primary_key=True, db_column='ID')
    id_aud_sql = models.IntegerField(null=True, blank=True, db_column='ID_AUD_SQL')
    id_aud_report = models.IntegerField(null=True, blank=True, db_column='ID_AUD_REPORT')
    id_aud_fv = models.IntegerField(null=True, blank=True, db_column='ID_AUD_FV')
    data_criacao = models.DateTimeField(auto_now_add=True, db_column='DATA_CRIACAO')
    criado_por = models.IntegerField(null=True, blank=True, db_column='CRIADO_POR')

    class Meta:
        managed = True
        db_table = 'Cadastro_Dependencias'

    def __str__(self):
        return f"{self.get_origem_display()} → {self.get_destino_display()}"

    def get_origem_display(self):
        if self.id_aud_sql: return f"SQL: {self.id_aud_sql}"
        if self.id_aud_report: return f"REP: {self.id_aud_report}"
        if self.id_aud_fv: return f"FV: {self.id_aud_fv}"
        return "—"

    def get_destino_display(self):
        if self.id_aud_sql and (self.id_aud_report or self.id_aud_fv):
            return f"SQL: {self.id_aud_sql}"
        if self.id_aud_report and (self.id_aud_sql or self.id_aud_fv):
            return f"REP: {self.id_aud_report}"
        if self.id_aud_fv and (self.id_aud_sql or self.id_aud_report):
            return f"FV: {self.id_aud_fv}"
        return "—"

    def clean(self):
        campos = [self.id_aud_sql, self.id_aud_report, self.id_aud_fv]
        preenchidos = sum(1 for c in campos if c is not None)
        if preenchidos != 2:
            raise ValidationError("Exatamente 2 campos devem ser preenchidos.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)