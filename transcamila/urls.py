from django.contrib import admin
from django.urls import path, include
from dashboard.views import login_view, logout_view, dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_view, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', include('dashboard.urls')),  # Inclui as URLs do app dashboard
]