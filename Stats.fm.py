import json
import inquirer
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from datetime import datetime, timedelta
import random

# Configure Spotify API authentication
client_id = 'df73a5aebc5446ce8c68468b5f661a71'
client_secret = 'c850e87c84334bba8b8c909504af3a03'
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Function to search for a Spotify track
def search_spotify_track(track_name, artist_name, album_name):
    query = f"track:{track_name} artist:{artist_name} album:{album_name}"
    result = sp.search(q=query, type='track', limit=1)
    if result['tracks']['items']:
        track = result['tracks']['items'][0]
        return {
            "spotify_track_uri": track['uri'],
            "master_metadata_track_name": track['name'],
            "master_metadata_album_artist_name": track['artists'][0]['name'],
            "master_metadata_album_album_name": track['album']['name'],
            "ms_played": track['duration_ms']
        }
    return None

# Function to search for random tracks from an artist
def search_spotify_artist_tracks(artist_name, limit=10):
    query = f"artist:{artist_name}"
    result = sp.search(q=query, type='track', limit=limit)
    tracks = []
    for item in result['tracks']['items']:
        tracks.append({
            "spotify_track_uri": item['uri'],
            "master_metadata_track_name": item['name'],
            "master_metadata_album_artist_name": item['artists'][0]['name'],
            "master_metadata_album_album_name": item['album']['name'],
            "ms_played": item['duration_ms']
        })
    return tracks

# Function to search for random tracks from an album
def search_spotify_album_tracks(album_name, limit=10):
    query = f"album:{album_name}"
    result = sp.search(q=query, type='album', limit=1)
    if result['albums']['items']:
        album_id = result['albums']['items'][0]['id']
        album_tracks = sp.album_tracks(album_id)
        tracks = []
        for item in album_tracks['items']:
            tracks.append({
                "spotify_track_uri": item['uri'],
                "master_metadata_track_name": item['name'],
                "master_metadata_album_artist_name": item['artists'][0]['name'],
                "master_metadata_album_album_name": album_name,
                "ms_played": item['duration_ms']
            })
        return tracks
    return []

# Function to adjust the timestamp based on ms_played
def adjust_timestamp(ts, ms_played, reverse=False):
    dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
    delta = timedelta(milliseconds=ms_played)
    if reverse:
        new_dt = dt - delta
    else:
        new_dt = dt + delta
    return new_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# Function to generate JSON entries
def generate_entries(username, track_infos, start_year, num_entries):
    start_date = datetime.strptime(f"{start_year}-01-01T08:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    max_date = datetime.strptime(f"{start_year}-12-25T23:59:59Z", "%Y-%m-%dT%H:%M:%SZ")

    data = []
    last_ts = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    for i in range(num_entries):
        track_info = random.choice(track_infos)
        template = {
            "ts": last_ts,
            "username": username,
            "platform": "android",
            "ms_played": track_info["ms_played"],
            "conn_country": "FR",
            "ip_addr_decrypted": "8.8.8.8",
            "user_agent_decrypted": "unknown",
            "master_metadata_track_name": track_info["master_metadata_track_name"],
            "master_metadata_album_artist_name": track_info["master_metadata_album_artist_name"],
            "master_metadata_album_album_name": track_info["master_metadata_album_album_name"],
            "spotify_track_uri": track_info["spotify_track_uri"],
            "episode_name": None,
            "episode_show_name": None,
            "spotify_episode_uri": None,
            "reason_start": "trackdone",
            "reason_end": "trackdone",
            "shuffle": True,
            "skipped": False,
            "offline": False,
            "offline_timestamp": 1715445864,
            "incognito_mode": False
        }

        current_time = datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%SZ")
        
        # For June, do not apply time restrictions
        if current_time.month == 6 or (current_time.time() < datetime.strptime("23:30:00", "%H:%M:%S").time() and current_time.time() > datetime.strptime("08:00:00", "%H:%M:%S").time()):
            data.append(template)
        else:
            print(f"Timestamp {last_ts} not added as it is between 23:30 and 08:00")

        last_ts = adjust_timestamp(last_ts, track_info["ms_played"])
        
        # Check if we go beyond 23:30 and adjust to resume at 08:00, except in June
        if current_time.month != 6 and datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%SZ").time() > datetime.strptime("23:30:00", "%H:%M:%S").time():
            next_day = datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%SZ").date() + timedelta(days=1)
            last_ts = f"{next_day}T08:00:00Z"
        
        # Check if we go beyond the max date
        if datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%SZ") > max_date:
            print(f"Reached the max date {last_ts}, stopping additions")
            break

    return data

# Interactive menu
questions = [
    inquirer.List('input_type', message="What would you like to input?", choices=['Track', 'Artist', 'Album']),
    inquirer.Text('username', message="Spotify username"),
    inquirer.Text('start_year', message="Start year", validate=lambda _, x: x.isdigit() and 1900 <= int(x) <= 2100),
    inquirer.Text('num_entries', message="Number of entries", validate=lambda _, x: x.isdigit() and int(x) > 0)
]

answers = inquirer.prompt(questions)
input_type = answers['input_type']
username = answers['username']
start_year = int(answers['start_year'])
num_entries = int(answers['num_entries'])

track_infos = []

if input_type == 'Track':
    num_tracks = int(inquirer.prompt([inquirer.Text('num_tracks', message="Number of different tracks", validate=lambda _, x: x.isdigit() and int(x) > 0)])['num_tracks'])
    for i in range(num_tracks):
        track_questions = [
            inquirer.Text(f'track_name_{i}', message=f"Track {i+1} name"),
            inquirer.Text(f'artist_name_{i}', message=f"Artist {i+1} name"),
            inquirer.Text(f'album_name_{i}', message=f"Album {i+1} name")
        ]
        track_answers = inquirer.prompt(track_questions)
        track_name = track_answers[f'track_name_{i}']
        artist_name = track_answers[f'artist_name_{i}']
        album_name = track_answers[f'album_name_{i}']

        track_info = search_spotify_track(track_name, artist_name, album_name)
        if track_info:
            track_infos.append(track_info)
        else:
            print(f"Track {track_name} by {artist_name} from album {album_name} not found on Spotify. Please check the information provided.")
            exit(1)
elif input_type == 'Artist':
    artist_name = inquirer.prompt([inquirer.Text('artist_name', message="Artist name")])['artist_name']
    track_infos = search_spotify_artist_tracks(artist_name, limit=50)
    if not track_infos:
        print(f"No tracks found for artist {artist_name}. Please check the information provided.")
        exit(1)
elif input_type == 'Album':
    album_name = inquirer.prompt([inquirer.Text('album_name', message="Album name")])['album_name']
    track_infos = search_spotify_album_tracks(album_name, limit=50)
    if not track_infos:
        print(f"No tracks found for album {album_name}. Please check the information provided.")
        exit(1)

# Generate the entries
entries = generate_entries(username, track_infos, start_year, num_entries)

# Save the entries to a JSON file
file_name = f'Streaming_History_Audio_{start_year}.json'
with open(file_name, 'w', encoding='utf-8') as file:
    json.dump(entries, file, ensure_ascii=False, indent=4)

print(f"{len(entries)} new entries successfully added to {file_name}.")
  
