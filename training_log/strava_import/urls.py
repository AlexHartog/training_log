from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='strava-index'),
    path('import_data', views.get_strava_data, name='strava-data'),
    path('auth', views.strava_auth, name='strava-auth'),
    path('auto_import/<int:enable>/', views.enable_auto_import, name='strava-auto-import'),
]
