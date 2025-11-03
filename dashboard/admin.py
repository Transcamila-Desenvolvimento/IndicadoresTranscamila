from django.contrib import admin
from .models import CTe

@admin.register(CTe)
class CTeAdmin(admin.ModelAdmin):
    list_display = (
        'numero_cte', 
        'serie_cte', 
        'nome_fantasia_emitente',
        'remetente', 
        'destinatario', 
        'tomador_info',  # NOVO: Informação do tomador
        'origem_destino',
        'data_emissao', 
        'valor_frete',
        'volumes',
        'peso'
    )
    
    list_filter = (
        'data_emissao',
        'cidade_origem',
        'cidade_destino',
        'uf_origem', 
        'uf_destino',
        'serie_cte',
        'nome_fantasia_emitente',
        'tomador_tipo',  # NOVO: Filtro por tipo de tomador
    )
    
    search_fields = (
        'numero_cte', 
        'chave_cte', 
        'remetente', 
        'destinatario',
        'cnpj_remetente',
        'cnpj_destinatario',
        'cidade_origem',
        'cidade_destino',
        'nome_fantasia_emitente',
        'razao_social_emitente',
        'tomador_razao_social',  # NOVO: Busca por tomador
        'tomador_cnpj',  # NOVO: Busca por CNPJ do tomador
    )
    
    readonly_fields = ('data_importacao', 'chave_cte', 'arquivo_xml', 'tomador_info')
    
    date_hierarchy = 'data_emissao'
    
    fieldsets = (
        ('Identificação do CTe', {
            'fields': (
                'numero_cte', 
                'serie_cte', 
                'chave_cte',
                'data_emissao'
            )
        }),
        ('Emitente (TRANSCAMILA)', {
            'fields': (
                'nome_fantasia_emitente',
                'razao_social_emitente',
                'cnpj_emitente',
            )
        }),
        ('Localidades', {
            'fields': (
                'cidade_origem',
                'uf_origem',
                'cidade_destino', 
                'uf_destino'
            )
        }),
        ('Empresas', {
            'fields': (
                'remetente',
                'cnpj_remetente',
                'destinatario',
                'cnpj_destinatario',
                'tomador_razao_social',  # NOVO: Tomador
                'tomador_cnpj',
                'tomador_tipo',
            )
        }),
        ('Valores', {
            'fields': (
                'valor_frete',
                'frete_peso',
                'advalorem',
                'pedagio',
                'gerenciamento_risco',
                'icms',
                'outros_valores',
            )
        }),
        ('Informações da Carga', {
            'fields': (
                'volumes',
                'peso'
            )
        }),
        ('Metadados', {
            'fields': (
                'data_importacao',
                'arquivo_xml',
                'tomador_info',  # NOVO: Info do tomador (readonly)
            ),
            'classes': ('collapse',)
        }),
    )
    
    def origem_destino(self, obj):
        return f"{obj.cidade_origem}/{obj.uf_origem} → {obj.cidade_destino}/{obj.uf_destino}"
    origem_destino.short_description = 'Origem → Destino'
    
    def tomador_info(self, obj):
        """Exibe informações resumidas do tomador"""
        if obj.tomador_razao_social:
            return f"{obj.tomador_razao_social} ({obj.tomador_tipo})"
        return "Não identificado"
    tomador_info.short_description = 'Tomador do Serviço'
    
    list_per_page = 50
    
    # Ordenação padrão por data de emissão (mais recentes primeiro)
    ordering = ('-data_emissao',)