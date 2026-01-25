import subprocess
import requests
import time
import json
import os
from pathlib import Path
from datetime import datetime  # Added for timestamps

# Configuration
FETCH_ALL = True
PLAYLIST_NAME = ""   # Specify the Playlist name if FETCH_ALL is False
PROJECT_DIR = Path(__file__).parent.resolve()
DB_PATH = PROJECT_DIR / "processed_songs.json"
BASE_URL = "https://itunes.apple.com/search"

def log(message):
    """Prints a message with a 2026-standard timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def open_music():
    """Ensures the Music app is running before processing."""
    log("Ensuring Apple Music is open...")
    # 'activate' opens the app if closed and brings it to focus
    # 'launch' opens it in the background if you prefer it to be silent
    script = 'tell application "Music" to launch'
    run_applescript(script)
    # Give the app 5 seconds to initialize its library
    time.sleep(10)

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, 'r') as f:
            return json.load(f)
    return []


def save_to_db(persistent_id):
    db = load_db()
    if persistent_id not in db:
        db.append(persistent_id)
        with open(DB_PATH, 'w') as f:
            json.dump(db, f)


def run_applescript(script):
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = process.communicate()
    return out.strip()


def get_japanese_metadata(song_name, artist):
    base_url = BASE_URL
    params = {"term": f"{song_name} {artist}", "country": "jp", "entity": "song", "limit": 1}
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if data.get('resultCount', 0) > 0:
            return data['results'][0]
    except:
        return None
    return None


# --- Main Logic ---
processed_ids = load_db()
log(f"Loaded {len(processed_ids)} previously processed songs.")

# 1. Ensure Music is open before we try to pull track data
open_music()

# 2. Fetch tracks from ALL user playlists
log("Scanning all user playlists for tracks...")
get_all_tracks_script = '''
tell application "Music"
    set out to ""
    set userPlaylists to (every playlist whose special kind is none)
    repeat with p in userPlaylists
        set theTracks to tracks of p
        repeat with t in theTracks
            set out to out & (persistent ID of t) & "|" & (name of t) & "|" & (artist of t) & "\n"
        end repeat
    end repeat
    return out
end tell
'''

# Fetch tracks for a specific play list
get_tracks_script = f'''
tell application "Music"
    set out to ""
    set theTracks to tracks of playlist "{PLAYLIST_NAME}"
    repeat with t in theTracks
        set out to out & (persistent ID of t) & "|" & (name of t) & "|" & (artist of t) & "\n"
    end repeat
    return out
end tell
'''

raw_tracks = ""
if FETCH_ALL is True:
    raw_tracks = run_applescript(get_all_tracks_script)
else:
    raw_tracks = run_applescript(get_tracks_script)

# 3. Unique processing (One song might be in multiple playlists)
seen_this_session = set()
track_lines = raw_tracks.split('\n')
log(f"Found {len(track_lines)} total entries across all playlists.")

process_count = 0
skipped_count = 0
for line in raw_tracks.split('\n'):
    if not line: continue
    p_id, name, artist = line.split('|')

    # Check if we've already done this song
    if p_id in processed_ids:
        skipped_count += 1
        # log(f"Skipping: {name} (Already in Japanese)")
        continue

    log(f"Processing: {name} by {artist}...")
    jp_data = get_japanese_metadata(name, artist)

    if jp_data:
        # 1. Escape Backslashes first (AppleScript's escape character)
        # 2. Escape Double Quotes (") which break AppleScript strings
        def escape_for_applescript(text):
            if not text: return ""
            return text.replace("\\", "\\\\").replace('"', '\\"')

        jp_title = escape_for_applescript(jp_data['trackName'])
        jp_album = escape_for_applescript(jp_data['collectionName'])
        jp_artist = escape_for_applescript(jp_data['artistName'])

        update_script = f'''
        tell application "Music"
            try
                -- 1. Explicitly find the track in the playlist context
                set t to (some track whose persistent ID is "{p_id}")
                
                -- 2. Force Add & Metadata Write
                -- Tahoe Workaround: Toggling 'favorited' forces a server-side handshake
                -- set favorited of t to true
                -- delay 0.5
                
                -- 3. Standard add command
                set libTrack to duplicate t to library playlist 1
                
                -- 4. Apply metadata to the NEW library version
                set name of libTrack to "{jp_title}"
                set sort name of libTrack to "{jp_title}"
                set album of libTrack to "{jp_album}"
                set artist of libTrack to "{jp_artist}"
                set sort artist of libTrack to "{jp_artist}"
                
                return "Success"
            on error
                return "Error or Already in Library"
            end try
        end tell
        '''
        res = run_applescript(update_script)
        if "Success" in res or "Already" in res:
            save_to_db(p_id)
            log(f"  -> Updated: {jp_title} by {jp_artist}")
            process_count += 1
        else:
            log(f"  -> {res}")
    else:
        log("  -> No Japanese metadata found.")

    time.sleep(1)  # Rate limit protection

log(f"Sync complete. Total processed: {process_count}. Total skipped: {skipped_count}")

