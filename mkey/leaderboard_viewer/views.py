# Create your views here.
import json
import re

import asyncio
from functools import partial

import requests
from django.shortcuts import render
from django.views import generic
from multiprocessing.pool import Pool

ACCESS_TOKEN_STRING = "&access_token=gebaggfxv5f9r2bjyzma3p2u"
GET_REALM_INFO_URL = "https://eu.api.battle.net/data/wow/realm/{0}?namespace=dynamic-eu&locale=en_GB"+ACCESS_TOKEN_STRING
GET_MYTHIC_LEADERBOARD_URL = "https://eu.api.battle.net/data/wow/connected-realm/{0}/mythic-leaderboard/?namespace=dynamic-eu&locale=en_GB"+ACCESS_TOKEN_STRING


class IndexView(generic.View):
    def get(self, request):
        return render(request, template_name='leaderboard_viewer/index.html')

    def post(self, request):
        try:
            realm_lowest_keys = get_realm_lowest_keys(request.POST["dungeon"], request.POST["wow_input"])
            error_message = ""
        except ValueError as error:
            realm_lowest_keys = None
            error_message = str(error)
        except:
            realm_lowest_keys = None
            error_message = "Something unexpected went terribly wrong. Yikes!"

        return render(request, 'leaderboard_viewer/index.html',
                      {"previous_player_input": request.POST["wow_input"], "realm_lowest_keys": realm_lowest_keys,
                       "dungeon_name": request.POST["dungeon"], "error_message": error_message})


class PlayerData:
    realm = ""
    name = ""

    def __init__(self, name, realm):
        self.name = name
        self.realm_regexp = re.compile('[A-Za-z][^A-Z]*')
        self.realm = self.git_real_realm_name(realm)

    def __str__(self):
        return "{0}-{1}".format(self.name, self.realm.capitalize())

    def git_real_realm_name(self, realm):
        # handle realms like Quel'Thalas, Anub'arak
        if "'" in realm:
            return realm.replace("'", "").lower()

        # handle realms like TarrenMill, GrimBatol
        return "-".join(self.realm_regexp.findall(realm)).lower()


DUNGEONS = {
    "Atal'dazar": 244,
    'Freehold': 245,
    'Tol Dagor': 246,
    'The MOTHERLODE!!': 247,
    'Waycrest Manor': 248,
    "Kings' Rest": 249,
    'Temple of Sethraliss': 250,
    'The Underrot': 251,
    'Shrine of the Storm': 252,
    'Siege of Boralus': 353
}


def get_realm_lowest_keys(dungeon, player_wow_input):
    dungeon_id = DUNGEONS[dungeon]
    player_wow_input = player_wow_input.strip()
    if not isinstance(player_wow_input, list):
        player_wow_input = player_wow_input.split("\n")
    players = []
    for player_input in player_wow_input:
        if "] " in player_input:
            # handles input copied from the game, this will be in the format of
            # [time] <Name>-<Realm>, and splits the input into [name, realm] for each player
            player_and_realm = player_input.split("] ")[1].strip().split("-")
        elif "-" in player_input:
            # handles when just the <Name>-<Realm> is provided
            player_and_realm = player_input.split("-")
        else:
            # handles when only the realm is specified
            player_and_realm = ["Vowyrin", player_input]

        # unpacks the list of 2 things -> [name, realm]
        player_data = PlayerData(*player_and_realm)
        players.append(player_data)

    p = Pool(min(5, len(player_wow_input)))

    # Create a queue that we will use to store our "workload".
    realm_data_requests = partial(retrieve_realm_data, dungeon_id)

    result = p.imap(realm_data_requests, players)

    p.close()
    p.join()

    realms_lowest_keys = []
    for r in result:
        realms_lowest_keys.append(r)

    # sort by key level
    return sorted(realms_lowest_keys, key=lambda x: x[1])


def retrieve_realm_data(dungeon_id, player):
    response = requests.get(GET_REALM_INFO_URL.format(player.realm))

    if response.status_code != 200:
        raise ValueError("Request to Blizzard did not succeed.")
    print(response.text)
    realm_info_json = json.loads(response.text)
    # +1 moves the index in front of the slash
    connected_id_start = realm_info_json["connected_realm"]["href"].rfind(
        "/") + 1
    connected_id_end = realm_info_json["connected_realm"]["href"].rfind("?")
    connected_id = realm_info_json["connected_realm"]["href"][
                   connected_id_start:connected_id_end]
    print("Connected realm id", connected_id)

    mythic_leaderboard_response = requests.get(
        GET_MYTHIC_LEADERBOARD_URL.format(connected_id))
    mythic_leaderboard_json = json.loads(mythic_leaderboard_response.text)

    for leaderboard in mythic_leaderboard_json["current_leaderboards"]:
        if leaderboard["id"] == dungeon_id:
            leaderboard_response = requests.get(leaderboard["key"]["href"] +
                                                "&" + ACCESS_TOKEN_STRING)
            leaderboard_json = json.loads(leaderboard_response.text)
            last_group = leaderboard_json["leading_groups"][-1]
            seconds = (last_group["duration"] / 1000) % 60
            minutes = (last_group["duration"] / (1000 * 60)) % 60
            print("Last group level", last_group["keystone_level"], "Duration",
                  "{0}m {1}s".format(minutes, seconds))
            return [str(player), last_group["keystone_level"], "{0}m {1}s".format(int(minutes), int(seconds))]
