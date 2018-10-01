from django.urls import path

from .views import IndexView

app_name = 'leaderboard_viewer'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
]
