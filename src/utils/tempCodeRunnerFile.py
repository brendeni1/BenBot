import os
import spotipy

from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

spotifyClient = spotipy.Spotify(
    auth_manager = SpotifyClientCredentials(
        client_id = SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)

def albumQuery(query: str, limit=5, type="album") -> list:
    if not query:
        raise ValueError("Album query is blank!")

    albumResults = spotifyClient.search(
        q=query,
        limit=limit,
        type=type
    )

    return albumResults

print(albumQuery("Ain't In It For My Health"))