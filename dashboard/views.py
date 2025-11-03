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

from django.http import JsonResponse
from datetime import date
from django.db.models import Sum

def api_ctes_dashboard(request):
    hoje = date.today()
    ctes_hoje = CTe.objects.filter(data_emissao__date=hoje).order_by('-data_emissao')[:10]

    total = CTe.objects.filter(data_emissao__date=hoje).count()
    valor_total = CTe.objects.filter(data_emissao__date=hoje).aggregate(total=Sum('valor_frete'))['total'] or 0
    media_frete = valor_total / total if total > 0 else 0
    peso_total = CTe.objects.filter(data_emissao__date=hoje).aggregate(total=Sum('peso'))['total'] or 0

    # Construir manualmente os campos calculados
    ultimos_ctes = []
    for cte in ctes_hoje:
        ultimos_ctes.append({
            'numero_cte': cte.numero_cte,
            'origem_destino': f"{cte.cidade_origem}/{cte.uf_origem} → {cte.cidade_destino}/{cte.uf_destino}",
            'tomador_info': f"{cte.tomador_razao_social} ({cte.tomador_tipo})" if cte.tomador_razao_social else "Não identificado",
            'valor_frete': float(cte.valor_frete),
            'data_emissao': cte.data_emissao.isoformat() if cte.data_emissao else None
        })

    data = {
        'total': total,
        'valor_total': float(valor_total),
        'media_frete': float(media_frete),
        'peso_total': float(peso_total),
        'ultimos_ctes': ultimos_ctes
    }

    return JsonResponse(data)