from django.contrib import admin
from django.urls import path, include
from dashboard.views import login_view, logout_view, dashboard_view
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('faturamento/Cte-FaturadosXafaturar/', views.cte_pendentes_view, name='cte'),
    path('faturamento/ctesfaturadosxafaturar/', views.cte_pendentes_view, name='cte'),
    path('faturamento/ctesrecebidos/', views.ctesrecebidos_view, name='cterecebidos'),
    path('faturamento/clientescominadimplência/', views.inadimplencia, name='inadimplencia'),
]