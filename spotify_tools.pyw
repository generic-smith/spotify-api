import threading
import time
import tkinter as tk
from tkinter import *

import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def api_connect():
    client_id = ''
    client_secret = ''
    client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)

    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    return sp


sp = api_connect()

selection_dict = {"None": None}
all_rows = []
most_recent_search = ""


def execute_search():
    search_button["state"] = DISABLED
    export_button["state"] = DISABLED
    start = time.time()
    artist = selection.get()
    most_recent_search = artist
    endpoint = endpoints.get()

    status_box.config(text="Searching: {} - {}".format(artist, endpoint))
    all_rows.clear()

    artist_uri = selection_dict[artist]
    artist_download = sp.artist(artist_uri)
    artist_name = artist_download["name"]
    artist_popularity = artist_download["popularity"]
    artist_genres = ", ".join(artist_download["genres"])
    artist_followers = artist_download["followers"]["total"]

    if endpoint == "Artist":
        row = {"Artist Name": artist_name,
               "Artist Popularity": artist_popularity,
               "Artist Genres": artist_genres,
               "Artist Followers": artist_followers,
               "Artist URI": artist_uri}
        all_rows.append(row)
        # print("Artist: {}".format(row))
    else:
        album_results = sp.artist_albums(artist_uri, album_type='album')

        # getting albums
        albums = album_results['items']
        # print(len(albums))
        while album_results['next']:
            album_results = sp.next(album_results)
            albums.extend(album_results['items'])

        for album in albums:
            album_uri = album["uri"]
            album_data = sp.album(album_uri)
            if endpoint == "Track":
                tracks = album_data['tracks']
                for track_basic in tracks['items']:
                    track = sp.track(track_basic["uri"])
                    row = {"Artist Name": artist_name,
                           "Artist Popularity": artist_popularity,
                           "Title": track["name"].upper(),
                           "Popularity": track["popularity"],
                           "Release Date": album_data["release_date"],
                           "Album": track["album"]["name"],
                           "Album Type": album_data["album_type"]}

                    if "isrc" in track["external_ids"]["isrc"]:
                        row["ISRC"] = track["external_ids"]["isrc"]["isrc"]
                    elif "isrc" in track["external_ids"]:
                        row["ISRC"] = track["external_ids"]["isrc"]
                    else:
                        row["ISRC"] = ""
                    row["Artist Genres"] = artist_genres
                    row["Markets"] = ", ".join(track["available_markets"])
                    row["Track URI"] = track["uri"]
                    # print("Track: {}".format(row))
                    all_rows.append(row)
            else:
                try:
                    upc = album_data["external_ids"]["upc"],
                    upc = str(upc).replace("(", "").replace(")", "").replace("'", "").replace(",", "")
                except KeyError:
                    upc = ''
                try:
                    label = album_data["label"]
                except KeyError:
                    label = ''
                row = {"Artist Name": artist_name,
                       "Artist Popularity": artist_popularity,
                       "Title": album_data['name'].upper(),
                       "Popularity": album_data['popularity'],
                       "Release Date": album_data["release_date"],
                       "Album Type": album_data["album_type"],
                       "Album UPC": upc,
                       "Album Label": label,
                       "Artist Genres": artist_genres,
                       "Album URI": album_data["uri"],
                       "Copyrights": album_data["copyrights"],
                       }
                # print("Album {}".format(row))
                all_rows.append(row)

    # output_text(status_box, "Found {} {}(s)".format(len(all_rows), endpoint))
    status_box.config(text="Found {} {}(s)".format(len(all_rows), endpoint))
    search_button["state"] = ACTIVE
    export_button["state"] = ACTIVE


# gets the unique spotify id for an artist based off of a user natural language search
def get_artist_options(*args):
    artist_name = user_search.get()
    status_box.config(text="Checking for '{}' on Spotify...".format(user_search.get()))
    if not artist_name == "":
        artist_data = sp.search(q=artist_name, type='artist', limit=9)
        for artist_name in artist_data['artists']['items']:
            selection_dict[artist_name["name"]] = artist_name['uri']
        search_button["state"] = ACTIVE
    return selection_dict.keys()


def refresh(*args):
    if user_search.get() == "rose gold":
        status_box.config(text="Rose gold mode")
        threading.Thread(target=rose_gold).start()
    else:
        # Reset var and delete all old options
        selection_menu['menu'].delete(0, 'end')
        selection_dict.clear()
        # Insert list of new options (tk._setit hooks them up to var)
        new_choices = get_artist_options()
        selection.set(get_first(new_choices))
        for choice in new_choices:
            selection_menu['menu'].add_command(label=choice, command=tk._setit(selection, choice))
        status_box.config(text="Autoselected '{}' in dropdown menu...".format(get_first(new_choices)))


def rose_gold():
    frame1 = "\n                                ~_~__~          " \
             "\n    []=     - ~_ - ~- /~~~~\\~~-       " \
             "\n    /            ~ - _ ~( '          |)~~-~      " \
             "\n                               \\ ~___/ ~-~~-~   "
    frame2 = "\n                               ~_~_~_          " \
             "\n    []=     ~ ~_- ~- /~~~~\\-~~       " \
             "\n    /               ~_ `- ( '          |)-~~-      " \
             "\n                               \\ ~___/ -~-~~-    "
    frame3 = "\n                               ~_~~_           " \
             "\n     []=     ~_- `~_- /~~~~\\~-~       " \
             "\n     /             ` _ ~- ( '          |)-~~-      " \
             "\n                               \\ ~___/ ~-~-~~    "
    while user_search.get() == "rose gold":
        output_window.after(ms=600, func=output_window.config(text=frame1))
        output_window.after(ms=600, func=output_window.config(text=frame2))
        output_window.after(ms=600, func=output_window.config(text=frame3))


def get_first(s):
    for e in s:
        return e


def export_data():
    artist_name = selection.get()
    exporting = pd.DataFrame(all_rows)
    try:
        filename = artist_name.replace("/", "-") + " " + endpoints.get() + " Data.csv"
        exporting.to_csv(filename, index=False)
        status_box.config(text="Output data to {}".format(filename))
    except:
        status_box.config(text="Error outputting CSV.")


def selection_updated(*args):
    status_box.config(text="Now viewing: {}".format(selection.get()))
    view_data()


def view_data():
    out = "\n\n\n\n"
    try:
        artist = selection.get()
        artist_uri = selection_dict[artist]
        artist_download = sp.artist(artist_uri)
        artist_name = artist_download["name"]
        artist_popularity = artist_download["popularity"]
        artist_genres = ", ".join(artist_download["genres"])
        artist_followers = artist_download["followers"]["total"]
        out = "Name: {}\nPopularity: {}\nFollowers: {}\nGenres: {}\nURI: {}".format(artist_name, artist_popularity,
                                                                                    artist_followers, artist_genres,
                                                                                    artist_uri)
    except BaseException as e:
        ouu = "Something went wrong! Artist data not found."
        status_box.config(text=ouu)

    output_window.config(text=out)


selection_list = ["None"]
dat = pd.DataFrame()

root = tk.Tk()
root.title("Spotify Tools (Beta Beware)")
mainframe = tk.Frame(root)
mainframe.pack(fill=BOTH, expand=True, padx=10, pady=10)

parameter_frame = tk.Frame(mainframe, borderwidth=2, relief="groove")
parameter_frame.pack(side=TOP, expand=False, fill=X)
parameter_search_frame = tk.Frame(parameter_frame)
parameter_search_frame.pack(side=LEFT, padx=10, pady=10)
parameter_selection_frame = tk.Frame(parameter_frame)
parameter_selection_frame.pack(side=LEFT, padx=10, pady=10)
parameter_endpoints_frame = tk.Frame(parameter_frame)
parameter_endpoints_frame.pack(side=LEFT, padx=10, pady=10)
output_frame = tk.Frame(mainframe, borderwidth=2, relief="groove")
output_frame.pack(side=TOP, expand=True, fill=BOTH, pady=10)
export_frame = tk.Frame(mainframe, height=80, borderwidth=2, relief="groove")
status_frame = tk.Frame(export_frame, borderwidth=2, relief="sunken")
status_frame.pack(side=LEFT, expand=True, fill=X, padx=(5, 10), pady=5)
export_frame.pack(side=TOP, expand=False, fill=X)

user_search = tk.StringVar()
tk.Label(parameter_search_frame, text="Search:").pack(side=LEFT)
user_search_entry = tk.Entry(parameter_search_frame, width=20, textvariable=user_search)
user_search_entry.pack(side=LEFT)
check_button = tk.Button(parameter_search_frame, text="Check", command=refresh)
check_button.pack(side=RIGHT, padx=10)
search_button = tk.Button(parameter_frame, text="Search",
                          command=lambda: threading.Thread(target=execute_search).start())
search_button.pack(side=RIGHT, padx=10)
search_button["state"] = DISABLED

selection = tk.StringVar()
selection.set(get_first(selection_list))
selection.trace("w", selection_updated)
tk.Label(parameter_selection_frame, text="Select Artist:").pack(side=LEFT, expand=True)
values = selection_list
selection_menu = tk.OptionMenu(parameter_selection_frame, selection, *values)
selection_menu.pack(side=LEFT, expand=True)

endpoints = tk.StringVar()
endpoints.set("Track")
tk.Label(parameter_endpoints_frame, text="Endpoints:").pack(side=LEFT, expand=True)
endpoint_options = {"Artist", "Album", "Track"}
endpoint_option = tk.OptionMenu(parameter_endpoints_frame, endpoints, *endpoint_options)
endpoint_option.pack(side=LEFT, expand=True)

# xscrollbar = Scrollbar(output_frame, orient=HORIZONTAL)
# xscrollbar.pack(side=BOTTOM, fill=X)
# yscrollbar = Scrollbar(output_frame)
# yscrollbar.pack(side=RIGHT, fill=Y)
# output_window = tk.Text(master=output_frame, wrap=NONE,
#                         xscrollcommand=xscrollbar.set,
#                         yscrollcommand=yscrollbar.set)
# output_window.pack(fill=BOTH, expand=True)
# xscrollbar.config(command=output_window.xview)
# yscrollbar.config(command=output_window.yview)
# stri = "%5s|%5s%5s\n".format("a", "b", "c")

output_window = tk.Label(master=output_frame, text='\n\n\n\n', justify=LEFT)
output_window.pack(side=LEFT, fill=BOTH)

status_box = tk.Label(master=status_frame, text='Standby')
status_box.pack(side=LEFT, expand=False, fill=Y, padx=10, pady=5)
view_button = tk.Button(export_frame, text="Preview Artist Endpoints", command=view_data)
export_button = tk.Button(export_frame, text="Export", command=export_data)
export_button.pack(side=RIGHT, pady=5, padx=10)
export_button["state"] = DISABLED
view_button.pack(side=RIGHT, pady=5)

# for child in mainframe.winfo_children():
#     child.grid_configure(padx=5, pady=5)
user_search_entry.focus()
root.bind('<Return>', refresh)

root.mainloop()
