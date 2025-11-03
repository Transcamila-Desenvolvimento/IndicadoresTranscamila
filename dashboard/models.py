from django.db import models

class CTe(models.Model):
    # Identificação básica
    numero_cte = models.CharField(max_length=50, db_index=True)
    serie_cte = models.CharField(max_length=10)
    chave_cte = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Localidades
    cidade_origem = models.CharField(max_length=100, db_index=True, default='')
    uf_origem = models.CharField(max_length=2, default='')
    cidade_destino = models.CharField(max_length=100, db_index=True, default='')
    uf_destino = models.CharField(max_length=2, default='')
    
    # Empresas
    remetente = models.TextField(db_index=True, default='')
    cnpj_remetente = models.CharField(max_length=20, blank=True, default='')
    destinatario = models.TextField(db_index=True, default='')
    cnpj_destinatario = models.CharField(max_length=20, blank=True, default='')
    
    # Tomador do serviço (aquele que PAGA o frete)
    tomador_razao_social = models.TextField(blank=True, default='')
    tomador_cnpj = models.CharField(max_length=20, blank=True, default='')
    tomador_tipo = models.CharField(max_length=50, blank=True, default='')  # remetente, destinatario, outro
    
    # Emitente (TRANSCAMILA)
    nome_fantasia_emitente = models.CharField(max_length=200, blank=True, default='')
    cnpj_emitente = models.CharField(max_length=20, blank=True, default='')
    razao_social_emitente = models.TextField(blank=True, default='')
    
    # Valores principais
    valor_frete = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frete_peso = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    advalorem = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    pedagio = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    outros_valores = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    icms = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gerenciamento_risco = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Informações da carga
    volumes = models.IntegerField(default=0)
    peso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Datas
    data_emissao = models.DateTimeField(db_index=True)
    data_importacao = models.DateTimeField(auto_now_add=True)
    
    # XML completo para referência
    arquivo_xml = models.TextField(blank=True)

    def __str__(self):
        return f"CTe {self.numero_cte} - {self.remetente}"

    class Meta:
        verbose_name = "CTe"
        verbose_name_plural = "CTes"
        indexes = [
            models.Index(fields=['data_emissao']),
            models.Index(fields=['cidade_origem', 'cidade_destino']),
            models.Index(fields=['nome_fantasia_emitente']),
            models.Index(fields=['tomador_cnpj']),
        ]

    @property
    def origem_destino(self):
        return f"{self.cidade_origem}/{self.uf_origem} → {self.cidade_destino}/{self.uf_destino}"

    @property
    def tomador_info(self):
        if self.tomador_razao_social:
            return f"{self.tomador_razao_social} ({self.tomador_tipo})"
        return "Não identificado"