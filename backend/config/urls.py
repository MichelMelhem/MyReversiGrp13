"""
URL configuration for config project.

``/api/...`` is the JSON API; every other route serves a page of the HTML/CSS
client from ``frontend/``.
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView


def page(template):
    return TemplateView.as_view(template_name=template)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', page('index.html'), name='home'),
    path('game/<uuid:game_id>/', page('game.html'), name='game-page'),
    path('history/', page('history.html'), name='history-page'),
    path('replay/<uuid:game_id>/', page('replay.html'), name='replay-page'),
    path('leaderboard/', page('leaderboard.html'), name='leaderboard-page'),
    path('rules/', page('rules.html'), name='rules-page'),
]
