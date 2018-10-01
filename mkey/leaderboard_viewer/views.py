# Create your views here.
from django.shortcuts import render
from django.views import generic

import muh_logic


class IndexView(generic.View):
    def get(self, request):
        return render(request, template_name='leaderboard_viewer/index.html')

    def post(self, request):
        realm_lowest_keys = muh_logic.get_realm_lowest_keys(request.POST["dungeon"], request.POST["wow_input"])
        return render(request, 'leaderboard_viewer/index.html',
                      {"previous_player_input": request.POST["wow_input"], "realm_lowest_keys": realm_lowest_keys})
