from django.contrib import admin
from django.urls import path
from attendance.views import landing_view, login_view, logout_view, register_view, dashboard_view, universal_webhook

urlpatterns = [
    path('', landing_view, name='landing'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('admin/', admin.site.urls),
    path('api/webhook/<uuid:token>/', universal_webhook, name='universal_webhook'),
]
