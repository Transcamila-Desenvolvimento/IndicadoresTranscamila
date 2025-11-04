from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
from .models import CTe


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Páginas de Faturamento
@login_required
def cte_pendentes_view(request):
    return render(request, 'indicadores/Faturamento/cte.html')
    return render(request, 'indicadores/Faturamento/cte.html')

@login_required
def ctesrecebidos_view(request):
    return render(request, 'indicadores/Faturamento/recebimento.html')

@login_required
def inadimplencia(request):
    return render(request, 'indicadores/Faturamento/inadimplencia.html')


@login_required
def op(request):
    return render(request, 'indicadores/Financeiro/op.html')

    
@login_required
def icms(request):
    return render(request, 'indicadores/Financeiro/icms.html')

@login_required
def nf(request):
    return render(request, 'indicadores/Financeiro/nf.html')

@login_required
def força(request):
    return render(request, 'indicadores/Recursos Humanos/forçadetrabalho.html')

@login_required
def jornada(request):
    return render(request, 'indicadores/Recursos Humanos/jornada.html')


@login_required
def recrutamento(request):
    return render(request, 'indicadores/Recursos Humanos/recrutamento.html')


@login_required
def avaliacaodeentregas(request):
    return render(request, 'indicadores/Provisao/avaldeentregas.html')


@login_required
def lancamento(request):
    return render(request, 'indicadores/Provisao/lancamento.html')


@login_required
def cte_pendentes_documentacao(request):
    return render(request, 'indicadores/Faturamento/cte_doc.html')

@login_required
def transcamilanews(request):
    return render(request, 'indicadores/Marketing/transcamilanews.html')

@login_required
def insightsinstagram(request):
    return render(request, 'indicadores/Marketing/instagram.html')

# dashboard/views.py
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime
from .models import CTe
import calendar

@staff_member_required
def api_ctes_dashboard(request):
    # === PARÂMETROS COM VALIDAÇÃO ===
    ano = request.GET.get('ano')
    mes = request.GET.get('mes')
    dia = request.GET.get('dia')  # formato: YYYY-MM-DD
    operacao = request.GET.get('operacao')
    tomador = request.GET.get('tomador')
    granularidade = request.GET.get('granularidade', 'dia')

    # === FILTROS BASE ===
    qs = CTe.objects.all()

    if ano:
        try:
            ano = int(ano)
            qs = qs.filter(data_emissao__year=ano)
        except ValueError:
            pass

    if mes:
        try:
            mes = int(mes)
            qs = qs.filter(data_emissao__month=mes)
        except ValueError:
            pass

    if dia:
        try:
            dia_dt = datetime.strptime(dia, '%Y-%m-%d')
            qs = qs.filter(data_emissao__year=dia_dt.year, data_emissao__month=dia_dt.month, data_emissao__day=dia_dt.day)
        except ValueError:
            pass

    if operacao:
        qs = qs.filter(tomador_tipo__icontains=operacao)

    if tomador:
        qs = qs.filter(tomador_cnpj=tomador)

    # === DADOS PRINCIPAIS ===
    totais = qs.aggregate(
        ctes=Count('id'),
        valor_faturado=Sum('valor_frete'),
        volume=Sum('volumes'),
        peso=Sum('peso')
    )

    # === COMPOSIÇÃO DO FRETE ===
    composicao = qs.aggregate(
        valor_faturado=Sum('valor_frete'),
        frete_peso=Sum('frete_peso'),
        advalorem=Sum('advalorem'),
        gerenciamento_risco=Sum('gerenciamento_risco'),
        icms=Sum('icms'),
        pedagio=Sum('pedagio')
    )

    # === SÉRIE TEMPORAL (SQLite-friendly) ===
    serie_temporal = []
    ctes_por_data = qs.values('data_emissao').annotate(
        ctes=Count('id'),
        valor_faturado=Sum('valor_frete')
    ).order_by('data_emissao')

    for item in ctes_por_data:
        data = item['data_emissao']
        if not data:
            continue
        if granularidade == 'dia':
            label = data.strftime('%d/%m')
        elif granularidade == 'semana':
            week = data.isocalendar()[1]
            label = f"{week:02d}/SEM"
        elif granularidade == 'mes':
            label = data.strftime('%m/%Y')
        else:
            label = data.strftime('%d/%m')

        serie_temporal.append({
            'label': label,
            'ctes': item['ctes'],
            'valor_faturado': float(item['valor_faturado'] or 0)
        })

    # === POR OPERAÇÃO E TOMADOR ===
    por_operacao = list(qs.values('tomador_tipo')
                        .annotate(valor=Sum('valor_frete'))
                        .order_by('-valor')[:10])
    for item in por_operacao:
        item['grupo'] = item.pop('tomador_tipo') or 'Não informado'
        item['valor'] = float(item['valor'] or 0)

    por_tomador = list(qs.values('tomador_cnpj', 'tomador_razao_social')
                       .annotate(valor=Sum('valor_frete'))
                       .order_by('-valor')[:10])
    for item in por_tomador:
        nome = item.pop('tomador_razao_social') or 'Não informado'
        item['grupo'] = f"{nome} ({item.pop('tomador_cnpj')})"
        item['valor'] = float(item['valor'] or 0)

    # === ÚLTIMOS CTEs ===
    ultimos_ctes = qs.order_by('-data_emissao')[:10]
    ultimos_ctes_list = []
    for cte in ultimos_ctes:
        ultimos_ctes_list.append({
            'numero_cte': cte.numero_cte,
            'origem_destino': cte.origem_destino,  # usa @property
            'tomador_info': cte.tomador_info,      # usa @property
            'valor_frete': float(cte.valor_frete),
            'data_emissao': cte.data_emissao.isoformat()
        })

    # === RESUMO ANALÍTICO ===
    resumo_analitico = list(qs.values('tomador_tipo')
                            .annotate(
                                ctes=Count('id'),
                                valor=Sum('valor_frete'),
                                peso=Sum('peso'),
                                volume=Sum('volumes')
                            ).order_by('-valor'))
    for item in resumo_analitico:
        item['tipo'] = 'Frete'
        item['grupo'] = item.pop('tomador_tipo') or 'Não informado'
        item['ctes'] = item['ctes']
        item['valor'] = float(item['valor'] or 0)
        item['peso'] = float(item['peso'] or 0)
        item['volume'] = item['volume']

    # === FILTROS DINÂMICOS ===
    operacaos = sorted(set(qs.values_list('tomador_tipo', flat=True).exclude(tomador_tipo='')))
    tomadors = sorted(set(qs.values_list('tomador_cnpj', flat=True).exclude(tomador_cnpj='')))

    # === RESPOSTA ===
    response = {
        'totais': {
            'ctes': totais['ctes'] or 0,
            'valor_faturado': float(totais['valor_faturado'] or 0),
            'volume': totais['volume'] or 0,
            'peso': float(totais['peso'] or 0)
        },
        'composicao': {k: float(v or 0) for k, v in composicao.items()},
        'serie_temporal': serie_temporal,
        'por_operacao': por_operacao,
        'por_tomador': por_tomador,
        'ultimos_ctes': ultimos_ctes_list,
        'resumo_analitico': resumo_analitico,
        'operacaos': operacaos,
        'tomadors': tomadors
    }

    return JsonResponse(response)
