#TODO
# Save playlist to profile (Dated?)
# Share saved playlist with second user? (Public?)
# Allow more than two users?
# Store last used playlist/user info to settings file
#   Allow overriding this file on run
# Upload basic settings file
# PKCE implementation?
#

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser

config = configparser.ConfigParser()
config.read("Settings.ini")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CREDENTIALS']['CLIENT_ID'],
                                               client_secret=config['CREDENTIALS']['CLIENT_SECRET'],
                                               redirect_uri=config['CREDENTIALS']['CLIENT_REDIRECT'],
                                               scope="playlist-read-private, playlist-modify-private"))

def getPlaylistIDs(entry, user, pl_list_id, pl_list_name):
    id_num = f"id{entry}"
    if (config['PLAYLIST'][id_num] != ""):
        if(config['PLAYLIST'][id_num] in pl_list_id):
            return config['PLAYLIST'][id_num]
    while(True):
        try:
            pl_name = input(f"Input desired playlist for {user}:")
            if pl_name in pl_list_name:
                return pl_list_id[pl_list_name.index(pl_name)]
            else:
                print(f"\'{pl_name}\" is not a valid playlist for {user}!")
        except:
            print("Invalid playlist name input!")

def buildLists(sp, user):
    # Build lists of playlist ids and names
    t_pl_list_id = []
    t_pl_list_name = []
    for cur_pl in sp.user_playlists(user)['items']:
        t_pl_list_id.append(cur_pl['id'])
        t_pl_list_name.append(cur_pl['name'])
    return t_pl_list_id, t_pl_list_name

def getUser(sp):
    username = input("Enter username")
    user = sp.user(username)
    return user

def loadTracks(sp, pl_one, pl_tracks):
    pl_result = sp.playlist_items(pl_one, fields='items.track, next', additional_types=['track'])
    pl_tracks.extend(pl_result['items'])

    while pl_result['next']:
        pl_result = sp.next(pl_result)
        pl_tracks.extend(pl_result['items'])



pl_list_id, pl_list_name = buildLists(sp, sp.me()['id'])
pl_one = getPlaylistIDs(1, sp.me()['display_name'], pl_list_id, pl_list_name)

user = getUser(sp)
pl_list_id, pl_list_name = buildLists(sp, user['id'])
pl_two = getPlaylistIDs(2, user['display_name'], pl_list_id, pl_list_name)

pl_tracks = []
loadTracks(sp, pl_one, pl_tracks)
print(len(pl_tracks))
loadTracks(sp, pl_two, pl_tracks)
print(len(pl_tracks))
