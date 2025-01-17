from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/med/', include('med_app.urls')),
    path('api/auth/', include('auth_app.urls')),
]