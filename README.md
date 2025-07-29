# Swap removed King Gizzard songs with Live versions still on spotify!
Here, I have made a tool which you can use with the spotify api to retain some gizz in your life. Note that not all songs have live versions available, so only ~70% of their discography can be swapped. Please Read the option relevant to you below.
NOTE: The band posted on instagram that bootlegging is allowed. To support KGLW, consider buying their studio recordings here-> https://kinggizzard.bandcamp.com

### Enjoy Listening! Feel Free to chip in a few bucks here https://coff.ee/guitarmattq
## Please star this repo if you found the tool helpful!
 If in the event their studio recordings return, I will make a tool which swaps back. Watch this repo for updates!
- Before you start! Consider transfering your playlists to a service where their music is still available. This will allow you to listen elsewhere to their studio recordings. I used https://soundiiz.com/webapp/playlists

## *Pre-Run* Get a free spotify API key
A Spotify API key is required per account. Visit https://developer.spotify.com/documentation/web-api/tutorials/getting-started
1. Log In (in the top right)
2. Visit the Dashboard (click your profile) and create an app.
3. Copy your Client API Key to the .env file in the run folder (either the unpacked zip or your python project). You can open it in Notepad++ or rename to .env.txt, edit it, then rename to .env.
4. Reveal your client secret. Copy this API key to the same .env.
5. Copy from here or the .env http://127.0.0.1:8888/callback into Redirect URLs on the Spotify App Webpage and click Add.
6. Save the Spotify App (at the bottom of the page).

## Option 1 (Windows) Run the .exe app package.
This is found in releases -> https://github.com/mattjohall/gizz_swapper_spotify/releases/tag/releases

Don't want to preview swaps? Just double click the .exe after putting keys in .env file.
1. Unzip the Release. This contains the .env example and a gizz-swapper.exe
2. Once in the unzipped folder on File Explorer, click File tab (top left) -> Powershell -> Open Powershell in the folder
3. run gizz_swapper.exe --simulate to preview swaps (this will open a browser, login to spotify and agree).
> gizz_swapper.exe

> Type y ENTER to continue.

Done!

## Option 2 (Python, any OS) 
1.  Clone this repository.
2.  Open the repo in your python shell. I recommend creating an env before installing requirements.
3.  Copy Client API key and Secret Key to .env file.
4.  Once cd into the folder, pip install -r requirements.txt
> python gizz_swapper.py --simulate (this will open a browser, login to spotify and agree).

or

> python gizz_swapper.py

> Type y ENTER to continue.
Done!

Lets keep the Gizz alive and available!
