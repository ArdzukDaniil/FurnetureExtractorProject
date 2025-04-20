# furniture_api/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Запросы к корню сайта ('/') будут идти в extractor.urls (теперь там только 'home')
    path('', include('extractor.urls')),
    # Подключение по /api/ УДАЛЕНО
]