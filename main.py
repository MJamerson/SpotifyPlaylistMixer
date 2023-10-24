import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = "b542dacb88154c8195acc2f76b5f01d5"
CLIENT_SECRET = "992fa59802a64a07a6a2b2c9c8e9119d"
CLIENT_REDIRECT = "http://localhost"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=CLIENT_REDIRECT,
                                               scope="playlist-read-private, playlist-modify-private"))


playlists = sp.user_playlists(sp.me()['id'])
for playlist in playlists['items']:
    print(playlist['name'])
