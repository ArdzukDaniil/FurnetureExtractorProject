# extractor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL для главной страницы с формой
    path('', views.home_view, name='home'), # Пустой путь '' означает корень этого приложения
    # Маршрут для extract_api УДАЛЕН
]