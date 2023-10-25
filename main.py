import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser

config = configparser.ConfigParser()
config.read("Settings.ini")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CREDENTIALS']['CLIENT_ID'],
                                               client_secret=config['CREDENTIALS']['CLIENT_SECRET'],
                                               redirect_uri=config['CREDENTIALS']['CLIENT_REDIRECT'],
                                               scope="playlist-read-private, playlist-modify-private"))

pl_id_list = sp.user_playlists(sp.me()['id'])
pl_id = ""
pl_tracks = []

for cur_pl in pl_id_list['items']:
    if cur_pl['name'] == "SharedInput":
        print(cur_pl['name'])
        pl_id = cur_pl['id']

pl_result = sp.playlist_items(pl_id, fields='items.track, next', additional_types=['track'])
pl_tracks.extend(pl_result['items'])

while pl_result['next']:
    pl_result = sp.next(pl_result)
    pl_tracks.extend(pl_result['items'])

print(len(pl_tracks))