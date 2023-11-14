#TODO
# Allow more than two users?
# Allow overriding settings  file on run
# Upload basic settings file
# Catch removed songs from Spotify and build report for user
# PKCE implementation?
# Set combination method (Pure random, 1x alternation, group alternation

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser
import logging
import sys
import time
import random
from itertools import chain, zip_longest

config = configparser.ConfigParser()
config.read("Settings.ini")
logging.basicConfig(level=logging.INFO)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CREDENTIALS']['CLIENT_ID'],
                                               client_secret=config['CREDENTIALS']['CLIENT_SECRET'],
                                               redirect_uri=config['CREDENTIALS']['CLIENT_REDIRECT'],
                                               scope="playlist-read-private, playlist-modify-private"))

def getEntryPlaylist(entry, u_name, pl_list_id, pl_list_name):
    user_section = f"USER{entry}"
# Implementation doesn't work if not on profile? Public non-profile playlist doesn't get found
#    if config[user_section]['pl_id'] in pl_list_id:
#        return config[user_section]['pl_id']
    if config[user_section]['pl_id'] != "":
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

def loadTracks(sp, pl_id_entry, pl_tracks_list, pl_track_IDs_lists):
    pl_result = sp.playlist_items(pl_id_entry, fields='items.track, next', additional_types=['track'])
    pl_tracks = []
    pl_track_IDs = []

    for item in pl_result['items']:
        if item['track']['id'] is not None:
            pl_tracks.extend(item)
            pl_track_IDs.append(item['track']['id'])

    while pl_result['next']:
        pl_result = sp.next(pl_result)
        for item in pl_result['items']:
            if item['track']['id'] is not None:
                pl_tracks.extend(item)
                pl_track_IDs.append(item['track']['id'])

    pl_tracks_list.append(pl_tracks)
    pl_track_IDs_lists.append(pl_track_IDs)

def createPlaylist(sp, user):
    pl_name = ""
    while pl_name == "":
        pl_name = input("Please enter playlist name: ")

    pl_new = sp.user_playlist_create(user, pl_name, public=False)
    config['PLAYLIST']['name'] = pl_name
    config['PLAYLIST']['id'] = pl_new['id']
    return pl_new['id']

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

def getExistingPlaylist(pl_list_name, pl_list_id):
    while True:
        pl_out_name = input("Existing playlist name: ")
        pl_out_id = getPlaylistID(pl_out_name, pl_list_name, pl_list_id)
        if pl_out_id != 0:
            return pl_out_id
        else:
            print(f"\'{pl_out_name}\" is not a valid playlist for {sp.me()['name']}!")

def buildOutputPlaylist(sp, pl_out_id, pl_track_IDs):
    sp.playlist_replace_items(pl_out_id, (pl_track_IDs.pop(0),))  # Pop the first element to replace existing playlist
    for group in chunker(pl_track_IDs, 100):
        while True: # Looping here allows for reattempting if ratelimiting is hit
            try:
                sp.playlist_add_items(pl_out_id, group)
                break
            except Exception as e:
                logging.warning(f"Rate limit hit, sleeping for 5 seconds: {e}")
                time.sleep(5)

def loadOutputPlaylist():
    if config['PLAYLIST']['id'] != "":
        return config['PLAYLIST']['id']
    else:
        return None

def getShuffleType():
    while True:
        valid_selections = ["1", "2"]
        shuffle_type = input("Shuffle methods:\n1) True shuffle\n2) Alternating shuffle\nSelection:")
        if shuffle_type in valid_selections:
            return int(shuffle_type)
        else:
            print("Please enter the number of your desired shuffle!")

def shuffleTrue(pl_track_IDs_lists):
    playlist_combined = []
    for playlist in pl_track_IDs_lists:
        random.shuffle(playlist)
        playlist_combined.extend(playlist)
    random.shuffle(playlist_combined)
    return playlist_combined

def shuffleAlternate(pl_track_IDs_lists): #https://stackoverflow.com/questions/48199961/how-to-interleave-two-lists-of-different-length
    return [x for x in chain(*zip_longest(*pl_track_IDs_lists)) if x is not None]


#Load OAuth user information and save to file
u1_name, u1_id = loadAuthUserInfo(sp)
pl_list_id, pl_list_name = buildLists(sp, u1_id)
pl_one = getEntryPlaylist(1, u1_name, pl_list_id, pl_list_name)
saveConfig()

# Load selected additional user information and save to file
u2_name, u2_id = loadUserInfo(sp, 2)
pl_list_id2, pl_list_name2 = buildLists(sp, u2_id)
pl_two = getEntryPlaylist(2, u2_name, pl_list_id2, pl_list_name2)
saveConfig()

logging.info("Loading playlist tracks... (This may take a minute)")
pl_tracks_list = []
pl_track_IDs_lists = []
loadTracks(sp, pl_one, pl_tracks_list, pl_track_IDs_lists)
print(f"Length of first playlist: {len(pl_track_IDs_lists[0])}")
loadTracks(sp, pl_two, pl_tracks_list, pl_track_IDs_lists)
print(f"Length of second playlist: {len(pl_track_IDs_lists[1])}")

pl_out_id = loadOutputPlaylist()
if pl_out_id is None:
    new_pl_flag = getNewPlaylistFlag()
    if new_pl_flag.upper() == "Y":
        pl_out_id = createPlaylist(sp, sp.me()['id'])
        saveConfig()
    else:
        pl_out_id = getExistingPlaylist(pl_list_name, pl_list_id)

shuffle_type = getShuffleType()
if shuffle_type == 1:
    pl_tracks_shuffled = shuffleTrue(pl_track_IDs_lists)
elif shuffle_type == 2:
    pl_tracks_shuffled = shuffleAlternate(pl_track_IDs_lists)



buildOutputPlaylist(sp, pl_out_id, pl_tracks_shuffled)


