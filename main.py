#TODO
# Use new playlist after creating it
# Rate limiting on playlist save
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

def getPlaylistIDList(entry, u_name, pl_list_id, pl_list_name):
    user_section = f"USER{entry}"
    if config[user_section]['pl_id'] in pl_list_id:
        return config[user_section]['pl_id']

    while(True):
        try:
            pl_name = input(f"Input desired playlist for {u_name}:")
            pl_id = getPlaylistID(pl_name, pl_list_name, pl_list_id)
            if(pl_id != 0):
                return pl_id
            else:
                print(f"\'{pl_name}\" is not a valid playlist for {u_name}!")
        except:
            print("Invalid playlist name input!")

def getPlaylistID(pl_name, pl_list_name, pl_list_id):
    if pl_name in pl_list_name:
        return pl_list_id[pl_list_name.index(pl_name)]
    else:
        return 0

def buildLists(sp, u_id):
    # Build lists of playlist ids and names
    t_pl_list_id = []
    t_pl_list_name = []
    for cur_pl in sp.user_playlists(u_id)['items']:
        t_pl_list_id.append(cur_pl['id'])
        t_pl_list_name.append(cur_pl['name'])
    return t_pl_list_id, t_pl_list_name

def getUser(sp):
    if config['USER2']['id'] != "":
        return config['USER2']['id']
    else:
        username = input("Enter username")
        user = sp.user(username)
        store_user = input("Save user to settings? (Y/N):")
        if store_user.upper() == "Y":
            saveUser(user, username)
        return user['id']

def saveConfig():
    with open("Settings.ini", "w") as configfile:
        config.write(configfile)

def loadTracks(sp, pl_one, pl_tracks, pl_track_IDs):
    pl_result = sp.playlist_items(pl_one, fields='items.track, next', additional_types=['track'])
    pl_tracks.extend(pl_result['items'])
    for item in pl_result['items']:
        pl_track_IDs.append(item['track']['id'])

    while pl_result['next']:
        pl_result = sp.next(pl_result)
        pl_tracks.extend(pl_result['items'])
        for item in pl_result['items']:
            pl_track_IDs.append(item['track']['id'])

def createPlaylist(sp, user):
    sp.user_playlist_create(user, "TestPlaylistPleaseIgnore", public=False, collaborative=False)

def chunker(seq, size): #https://stackoverflow.com/questions/434287/how-to-iterate-over-a-list-in-chunks
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def loadUserInfo(sp, id_num):
    id_num = f"USER{id_num}"
    try:
        u_user = config[id_num]['user']
        u_name = config[id_num]['name']
        u_id = config[id_num]['id']
    except:
        return None, None, None

    promptSave = False
    while u_user == "":
        try:
            u_user = input("Enter username")
            t_acc = sp.user(u_user)
            promptSave = True
        except:
            print("Error loading user information! Please double check the username provided!")

    if u_name == "":
        try:
            u_name = t_acc['name']
            promptSave = True
        except:
            print("Error accessing name of user object!")
            u_name = None

    if u_id == "":
        try:
            u_id = t_acc['id']
            promptSave = True
        except:
            print("Error accessing id of user object!")
            u_id = None

    if promptSave:
        save_user = input("Save user to settings? (Y/N):")
        if save_user.upper() == "Y":
            saveUser(id_num, u_user, u_name, u_id)

    return u_user, u_name, u_id

def loadPlaylistInfo(sp, id_num, u_name):
    id_num = f"USER{id_num}"
    try:
        u_pl_name = config[id_num]['pl_name']
        u_pl_id = config[id_num]['pl_id']
    except:
        print("TODO Error handle")
    while u_pl_name == "":
        try:
            u_pl_name = input(f"Enter playlist name of {u_name}: ")
        except:
            print("Error loading playlist information! Please double check the username provided!")

    store_user = input("Save user to settings? (Y/N):")
        if store_user.upper() == "Y":
            saveUser(user, username)

def loadAuthUserInfo(sp):
    user_section = "USER1"
    try:
        if config[user_section]['name'] == "" or config[user_section]['id'] == "":
            t_acc = sp.me()
            config[user_section]['name'] = t_acc['display_name']
            config[user_section]['id'] = t_acc['id']
            saveConfig()
    except:
        print("Unable to load/save default user!")
        sys.exit(1) # TODO: Menu Interface: Remove and return

    return config[user_section]['name'], config[user_section]['id']





u1_name, u1_id = loadAuthUserInfo(sp)
pl_list_id, pl_list_name = buildLists(sp, u1_id)
pl_one = getPlaylistIDList(1, u1_name, pl_list_id, pl_list_name)
# TODO: Auth user is not saving playlist information!

user = getUser(sp)
pl_list_id2, pl_list_name2 = buildLists(sp, user)
pl_two = getPlaylistIDList(2, user['display_name'], pl_list_id2, pl_list_name2)

pl_tracks = []
pl_track_IDs = []
loadTracks(sp, pl_one, pl_tracks, pl_track_IDs)
print(len(pl_tracks))
loadTracks(sp, pl_two, pl_tracks, pl_track_IDs)
print(len(pl_tracks))
print(len(pl_track_IDs))

while True:
    new_pl_flag = input("Create new playlist? (Y/N): ")
    if new_pl_flag.upper() == "Y" or new_pl_flag.upper() == "N":
        break;
    else:
        print("Please enter valid choice.")

if new_pl_flag.upper() == "Y":
    createPlaylist(sp, sp.me()['id'])
else:
    while True:
        try:
            pl_out_name = input("Existing playlist name: ")
            pl_out_id = getPlaylistID(pl_out_name, pl_list_name, pl_list_id)
            if (pl_out_id != 0):
                sp.playlist_replace_items(pl_out_id, (pl_track_IDs.pop(0), )) # Pop the first element to replace existing playlist
                for group in chunker(pl_track_IDs, 100):
                    sp.playlist_add_items(pl_out_id, group)
                break
            else:
                print(f"\'{pl_out_name}\" is not a valid playlist for {sp.me()['name']}!")
        except:
            print("Invalid playlist name input!")



