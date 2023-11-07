#TODO
# Use new playlist after creating it
# Allow more than two users?
# Allow overriding settings  file on run
# Upload basic settings file
# Catch removed songs from Spotify and build report for user
# PKCE implementation?
#

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import logging
import sys
import time

config = configparser.ConfigParser()
config.read("Settings.ini")
logging.basicConfig(level=logging.WARNING)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CREDENTIALS']['CLIENT_ID'],
                                               client_secret=config['CREDENTIALS']['CLIENT_SECRET'],
                                               redirect_uri=config['CREDENTIALS']['CLIENT_REDIRECT'],
                                               scope="playlist-read-private, playlist-modify-private"))

def getEntryPlaylist(entry, u_name, pl_list_id, pl_list_name):
    user_section = f"USER{entry}"
    if config[user_section]['pl_id'] in pl_list_id:
        return config[user_section]['pl_id']

    while True:
        try:
            pl_name = input(f"Input desired playlist for {u_name}:")
            pl_id = getPlaylistID(pl_name, pl_list_name, pl_list_id)
            if pl_id != 0:
                config[user_section]['pl_name'] = pl_name
                config[user_section]['pl_id'] = pl_id
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

def saveConfig():
    with open("Settings.ini", "w") as configfile:
        config.write(configfile)

def loadTracks(sp, pl_one, pl_tracks, pl_track_IDs):
    pl_result = sp.playlist_items(pl_one, fields='items.track, next', additional_types=['track'])
    #pl_tracks.extend(pl_result['items'])
    for item in pl_result['items']:
        if item['track']['id'] != None:
            pl_tracks.extend(item)
            pl_track_IDs.append(item['track']['id'])

    while pl_result['next']:
        pl_result = sp.next(pl_result)
        for item in pl_result['items']:
            if item['track']['id'] != None:
                pl_tracks.extend(item)
                pl_track_IDs.append(item['track']['id'])

def createPlaylist(sp, user):
    sp.user_playlist_create(user, "TestPlaylistPleaseIgnore", public=False, collaborative=False)

def chunker(seq, size): #https://stackoverflow.com/questions/434287/how-to-iterate-over-a-list-in-chunks
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

def loadUserInfo(sp, id_num):
    id_num = f"USER{id_num}"

    u_user = config[id_num]['user']
    u_name = config[id_num]['name']
    u_id = config[id_num]['id']

    try:
        t_acc = sp.user(u_user)
        if t_acc['display_name'] == u_name and t_acc['id'] == u_id:
            return t_acc['display_name'], t_acc['id']
        else:
            raise Exception
    except:
        while True: # Loop until a valid user, name, and id have been collected
            try:
                u_user = input("Enter username: ")
                t_acc = sp.user(u_user)
            except:
                print("Error loading user information! Please double check the username provided!")
                continue

            if u_name == "" or u_id == "":
                try:
                    u_name = t_acc['display_name']
                    u_id = t_acc['id']
                    break
                except:
                    print("Error accessing name or id of user object!")

        # Store user values to config memory for saving later
    config[id_num]['user'] = u_user
    config[id_num]['name'] = u_name
    config[id_num]['id'] = u_id
    return u_name, u_id

def loadAuthUserInfo(sp):
    user_section = "USER1"
    try:
        if config[user_section]['name'] == "" or config[user_section]['id'] == "":
            t_acc = sp.me()
            config[user_section]['name'] = t_acc['display_name']
            config[user_section]['id'] = t_acc['id']
    except:
        print("Unable to load/save default user!")
        sys.exit(1) # TODO: Menu Interface: Remove and return

    return config[user_section]['name'], config[user_section]['id']

def getNewPlaylistFlag():
    while True:
        pl_flag = input("Create new playlist? (Y/N): ")
        if pl_flag.upper() == "Y" or pl_flag.upper() == "N":
            return pl_flag
        else:
            print("Please enter valid choice.")



# Load OAuth user information and save to file
u1_name, u1_id = loadAuthUserInfo(sp)
pl_list_id, pl_list_name = buildLists(sp, u1_id)
pl_one = getEntryPlaylist(1, u1_name, pl_list_id, pl_list_name)
saveConfig()

# Load selected additional user information and save to file
u2_name, u2_id = loadUserInfo(sp, 2)
pl_list_id2, pl_list_name2 = buildLists(sp, u2_id)
pl_two = getEntryPlaylist(2, u2_name, pl_list_id2, pl_list_name2)
saveConfig()

pl_tracks = []
pl_track_IDs = []
loadTracks(sp, pl_one, pl_tracks, pl_track_IDs)
logging.debug(f"Length after first playlist: {len(pl_tracks)}")
loadTracks(sp, pl_two, pl_tracks, pl_track_IDs)
logging.debug(f"Length after second playlist: {len(pl_tracks)}")
logging.debug(f"Length of playlist ids: {len(pl_track_IDs)}")

new_pl_flag = getNewPlaylistFlag()

if new_pl_flag.upper() == "Y":
    createPlaylist(sp, sp.me()['id'])
else:
    while True:
        pl_out_name = input("Existing playlist name: ")
        pl_out_id = getPlaylistID(pl_out_name, pl_list_name, pl_list_id)
        if pl_out_id != 0:
            sp.playlist_replace_items(pl_out_id, (pl_track_IDs.pop(0), )) # Pop the first element to replace existing playlist
            for group in chunker(pl_track_IDs, 100):
                while True:
                    try:
                        print(group)
                        sp.playlist_add_items(pl_out_id, group)
                        break
                    except Exception as e:
                        logging.warning(f"Rate limit hit, sleeping for 5 seconds: {e}")
                        time.sleep(5)
            break
        else:
            print(f"\'{pl_out_name}\" is not a valid playlist for {sp.me()['name']}!")



