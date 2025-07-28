import spotipy
from spotipy.oauth2 import SpotifyOAuth
from rapidfuzz import fuzz
from tabulate import tabulate
from dotenv import load_dotenv
import os
import re
import argparse
import time

load_dotenv()  # Load from .env file
def parse_args():
    parser = argparse.ArgumentParser(description="Replace King Gizzard tracks with live bootlegs in your playlists.")
    parser.add_argument('--simulate', action='store_true', help='Simulate changes without modifying playlists.')
    return parser.parse_args()

# === CONFIGURATION === #
TARGET_ARTIST = "King Gizzard & The Lizard Wizard"
LIVE_KEYWORDS = ["live", "bootleg"]
FUZZY_MATCH_THRESHOLD = 60
SEARCH_LIMIT = 20
global SIMULATE
#SIMULATE = True  # Set True for dry-run mode (no playlist edits)

# === AUTH SETUP === #
scope = "playlist-read-private playlist-modify-private playlist-modify-public"

print("Loading environment variables for Spotify credentials...")
sp_oauth = SpotifyOAuth(
    scope=scope,
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI")
)
print("SpotifyOAuth object created.")

print("Creating Spotify client...")

import requests
from requests.adapters import HTTPAdapter
from requests import Session

class TimeoutSession(Session):
    def __init__(self, timeout=10):
        super().__init__()
        self.timeout = timeout

    def request(self, *args, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return super().request(*args, **kwargs)

# Create session with retry logic (optional)
session = TimeoutSession(timeout=10)
adapter = HTTPAdapter(max_retries=3)
session.mount("https://", adapter)
sp = spotipy.Spotify(auth_manager=sp_oauth, requests_session=session)
print("Spotify client ready.")

def normalize_title(title):
    # Lowercase, remove punctuation, and collapse spaces
    title = re.sub(r'\([^)]*\)', '', title)  # remove things like (Live...)
    title = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())  # remove punctuation
    return re.sub(r'\s+', ' ', title).strip()

def tokenize(title):
    return set(normalize_title(title).split())

def is_strict_match(original, candidate, fuzzy_threshold=85):
    original_norm = normalize_title(original)
    candidate_norm = normalize_title(candidate)
    
    # Quick fuzzy score check
    score = fuzz.token_set_ratio(original_norm, candidate_norm)
    if score < fuzzy_threshold:
        return False

    # Tokenized word match
    original_words = tokenize(original)
    candidate_words = tokenize(candidate)

    # Must contain *all* or *most* of the original words
    overlap = original_words.intersection(candidate_words)
    match_ratio = len(overlap) / len(original_words)

    print(f"[MATCH CHECK] '{original}' ↔ '{candidate}': score={score}, overlap={overlap}, ratio={match_ratio:.2f}")
    
    return match_ratio >= 0.8  # stricter than just 1 word

BAD_MATCHES = [
    ("I’m Not a Man Unless I Have A Woman", "I'm Not in Your Mind (Live at Red Rocks '22)"),
    ("King Gizzard & the Lizard Wizard W/King Stingray - Treaty (Live in Austin '24)", None),  # Reject any match TO this
]

def is_bad_match(original, candidate):
    for bad_original, bad_candidate in BAD_MATCHES:
        if original == bad_original and (bad_candidate is None or candidate == bad_candidate):
            return True
        if bad_candidate is None and candidate == bad_original:  # If we want to reject anything matching a specific track
            return True
    return False


def is_gizzard(track):
    artist_name = track['artists'][0]['name'].lower()
    result = TARGET_ARTIST.lower() in artist_name
    #print(f"Checking artist '{artist_name}' for target match: {result}")
    return result

def find_best_live_version(title):
    query = f"{title} {TARGET_ARTIST} live"
    for attempt in range(3):
        try:
            results = sp.search(q=query, type='track', limit=SEARCH_LIMIT)
            break  # Success!
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Search attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
            else:
                return None
    tracks = results['tracks']['items']

    if not tracks:
        #print("No search results.")
        return None

    def is_bootleg_candidate(track):
        artist_name = track['artists'][0]['name'].lower()
        album_name = track['album']['name'].lower()
        track_name = track['name'].lower()
        # Check bootleg in artist or album
        if "bootleg" not in artist_name and "bootleg" not in album_name:
            return False
        # Check 'live' or 'bootleg' in track title
        if not any(word in track_name for word in LIVE_KEYWORDS):
            return False
        return True

    norm_title = normalize_title(title)

    # Check first result immediately
    # Check first result only if it's a bootleg *and* matches closely
    first_track = tracks[0]
    if is_bootleg_candidate(first_track):
        norm_first = normalize_title(first_track['name'])
        score = fuzz.token_set_ratio(norm_title, norm_first)
        print(f"Top search result '{first_track['name']}' score: {score}")
        if score >= FUZZY_MATCH_THRESHOLD:
            #print(f"Using top search result: '{first_track['name']}'")
            return first_track
        else:
            print(f"XXXX Top result '{first_track['name']}' rejected due to low score.")


    for track in tracks:
        if is_bootleg_candidate(track):
            candidate_title = track['name']
            if is_strict_match(title, candidate_title):
                print(f"\OoO/ Accepted match: '{title}' → '{candidate_title}'")
                return track


def get_user_playlists():
    print("Fetching user playlists...")
    results = sp.current_user_playlists()
    playlists = results['items']
    print(f"Found {len(playlists)} playlists.")
    return playlists


def replace_tracks_in_playlist(playlist):
    name = playlist['name']
    print(f"\n Processing playlist: '{name}'")
    playlist_id = playlist['id']
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']

    swaps = []
    failed = []

    for index, item in enumerate(tracks):
        track = item['track']
        if track is None:
            print(f" -> Skipping index {index}: Track is None")
            continue

        if is_gizzard(track):
            title = track['name']
            live_version = find_best_live_version(title)
            if is_bad_match(title, live_version):
                continue
            if live_version:
                print(f"--> Swapping '{title}' at position {index} with '{live_version['name']}'")
                if not SIMULATE:
                    try:
                        # Remove specific occurrence at this index
                        sp.playlist_remove_specific_occurrences_of_items(
                            playlist_id,
                            [{"uri": track['uri'], "positions": [index]}]
                        )
                        # Insert the live version at the same index
                        sp.playlist_add_items(
                            playlist_id,
                            [live_version['uri']],
                            position=index
                        )
                    except Exception as e:
                        print(f"ERRR: Error swapping at index {index}: {e}")
                        failed.append(title)
                        continue
                else:
                    print("Simulation mode ON: swap not executed.")
                swaps.append((title, live_version['name']))
            else:
                print(f"XX No bootleg match found for '{title}'")
                failed.append(title)

    return name, swaps, failed


def main():
    global SIMULATE
    if not SIMULATE:
        confirm = input("WARN: This will modify your playlists. Proceed? No shows simulated output. (y/N): ").strip().lower()
        SIMULATE = False
        if confirm != 'y':
            SIMULATE = True
    playlists = get_user_playlists()
    report = []

    total_gizz_tracks = 0
    total_swapped = 0

    for playlist in playlists:
        name, swaps, failed = replace_tracks_in_playlist(playlist)

        gizz_count = len(swaps) + len(failed)
        total_gizz_tracks += gizz_count
        total_swapped += len(swaps)

        if gizz_count > 0:
            report.append({
                "playlist": name,
                "swapped": swaps,
                "not_found": failed
            })

    print("\n\nFINAL REPORT")
    if not report:
        print("No King Gizzard songs found in any playlists.")
        return

    for r in report:
        print(f"\n🎵 Playlist: {r['playlist']}")
        if r['swapped']:
            print("Swapped:")
            print(tabulate(r['swapped'], headers=["Original", "Live Version"]))
        else:
            print("Swapped: None")

        if r['not_found']:
            print("\nNot Found:")
            for nf in r['not_found']:
                print(f" - {nf}")
        else:
            print("Not Found: None")

    print("\nSUMMARY")
    print(f"Total King Gizzard tracks found: {total_gizz_tracks}")
    print(f"Total swapped with bootlegs: {total_swapped}")
    if total_gizz_tracks > 0:
        percent = (total_swapped / total_gizz_tracks) * 100
        print(f"✅ Match rate: {percent:.2f}%")


if __name__ == "__main__":
    args = parse_args()
    global SIMULATE
    SIMULATE = args.simulate
    main()
