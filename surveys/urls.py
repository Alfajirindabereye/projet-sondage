from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    path('', views.home, name='home'),
    path('mes-sondages/', views.dashboard, name='dashboard'),
    path('sondages/nouveau/', views.survey_builder, name='create'),
    path('sondages/<int:pk>/modifier/', views.survey_builder, name='edit'),
    path('sondages/<int:pk>/basculer/', views.survey_toggle_close, name='toggle_close'),
    path('sondages/<int:pk>/supprimer/', views.survey_delete, name='delete'),
    path('sondages/<int:pk>/resultats/', views.survey_results, name='results'),
    path('sondages/<int:pk>/export.csv', views.survey_export_csv, name='export_csv'),
    path('s/<uuid:token>/', views.survey_detail, name='detail'),
    path('s/<uuid:token>/merci/', views.survey_thanks, name='thanks'),
]
