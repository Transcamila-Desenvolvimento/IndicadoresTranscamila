from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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
