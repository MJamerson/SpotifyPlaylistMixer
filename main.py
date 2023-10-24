import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = ""
CLIENT_SECRET = ""
CLIENT_REDIRECT = "http://localhost"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=CLIENT_REDIRECT,
                                               scope="playlist-read-private, playlist-modify-private"))


playlists = sp.user_playlists(sp.me()['id'])
for playlist in playlists['items']:
    print(playlist['name'])
