from django.contrib import admin
from django.urls import path, include
from dashboard.views import login_view, logout_view, dashboard_view
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('faturamento/ctesfaturadosxafaturar/', views.cte_pendentes_view, name='cte'),
    path('faturamento/ctesfaturadosxafaturar/documentacao', views.cte_pendentes_documentacao, name='cte_pendentes_documentacao'),
    path('faturamento/ctesrecebidos/', views.ctesrecebidos_view, name='cterecebidos'),
    path('faturamento/clientescominadimplência/', views.inadimplencia, name='inadimplencia'),
    path('financeiro/Statusdeops/', views.op, name='op'),
    path('financeiro/ICMSporConformidade/', views.icms, name='icms'),
    path('financeiro/pagamentossemlanlcamento/', views.nf, name='nf'),
    path('recursoshumanos/distribuicaodaforcadetrabalho/', views.força, name='força'),
    path('recursoshumanos/jornada/', views.jornada, name='jornada'),
    path('recursoshumanos/recrutamentoeselecao/', views.recrutamento, name='recrutamento'),
    path('provisao/avaliacaodeentregas/', views.avaliacaodeentregas, name='avaliacaodeentregas'),
    path('provisao/lancamentoaeepc/', views.lancamento, name='lancamento'),
    path('marketing/transcamilanews/', views.transcamilanews, name='transcamilanews'),
    path('marketing/insightsinstagram/', views.insightsinstagram, name='insightsinstagram'),
]