import os
from datetime import datetime
from uuid import uuid4
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.utils import dates

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

spotifyClient = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)

class Artist:
    def __init__(self, spotifyID: str, name: str, link: str):
        self.spotifyID = spotifyID
        self.name = name
        self.link = link

class Track:
    def __init__(
        self,
        spotifyID: str,
        name: str,
        artists: list[Artist],
        explicit: bool,
        link: str,
        trackNumber: int,
        durationMS: int,
        rating: float = None
    ):
        self.spotifyID = spotifyID
        self.name = name
        self.artists = artists
        self.explicit = explicit
        self.link = link
        self.trackNumber = trackNumber
        self.durationMS = durationMS
        self.rating = rating

    def setRating(self, rating: float) -> None:
        self.rating = rating

        return

    def getArtists(self, formatted: bool = False) -> Artist | str:
        if formatted:
            return ", ".join([artist.name for artist in self.artists])
        else:
            return self.artists

class Album:
    def __init__(
        self,
        spotifyID: str,
        name: str,
        artists: list[Artist],
        link: str,
        releaseDate: datetime,
        createdBy: int,
        createdAt: datetime = dates.simpleDateObj(timeNow=True),
        editedAt: datetime = None,
        tracks: list[Track] = [],
        coverImage: str = None
    ):
        self.ratingID = uuid4(),
        self.spotifyID = spotifyID
        self.name = name
        self.artists = artists
        self.link = link
        self.releaseDate = releaseDate
        self.createdBy = createdBy
        self.createdAt = createdAt
        self.editedAt = editedAt
        self.tracks = tracks
        self.coverImage = coverImage

    def totalTracks(self) -> int:
        return len(self.tracks)

    def meanRating(self) -> float:
        if not self.tracks:
            raise Exception("There are no tracks assigned to the album so there is no average rating!")
        
        cleanedRatingList: list[float] = []

        for track in self.tracks:
            if (track.rating >= 0) and (track.rating <= 10):
                cleanedRatingList.append(track.rating)
            elif track.rating == -1:
                continue
            elif track.rating == None:
                raise ValueError("There is an unrated song in the album rating and an average could not be calculated! Please finish the rating.")
        
        mean = round(sum(cleanedRatingList) / len(cleanedRatingList), 1)

        return mean
    
    def serializeRating(self) -> bytes:
        serialized = pickle.dumps(self)

        return serialized
    
    def addTrack(self, track: Track):
        self.tracks.append(track)

    def getArtists(self, formatted: bool = False) -> Artist | str:
        if formatted:
            return ", ".join([artist.name for artist in self.artists])
        else:
            return self.artists

def searchForAlbumName(query: str, limit=5, type="album") -> list:
    if not query:
        raise ValueError("utils > music.py > albumQuery: Album query is blank!")

    albumResults = spotifyClient.search(q=query, limit=limit, type=type)

    return albumResults

def fetchAlbumDetailsByID(albumID: str) -> dict:
    if not albumID:
        raise ValueError("utils > music.py > albumDetails: Album ID is blank!")

    albumResults = spotifyClient.album(album_id=albumID)

    return albumResults

def parseAlbumDetails(data: dict, createdBy: int, createdAt: datetime = None) -> Album:
    if not data:
        raise ValueError("No data provided to album parser.")
    
    spotifyID = data["id"]
    name = data["name"]
    artists = [Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"]) for artist in data["artists"]]
    link = data["external_urls"]["spotify"]
    releaseDate = dates.simpleDateObj(data["release_date"])
    
    tracks = []

    for trackData in data["tracks"]["items"]:
        trackArtists = [Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"]) for artist in trackData["artists"]]

        track = Track(
            trackData["id"],
            trackData["name"],
            trackArtists,
            trackData["explicit"],
            trackData["external_urls"]["spotify"],
            trackData["track_number"],
            trackData["duration_ms"],
        )
    
        tracks.append(track)

    coverImage = None if not data["images"] else data["images"][0]["url"]

    album = Album(
        spotifyID,
        name,
        artists,
        link,
        releaseDate,
        createdBy,
        createdAt if createdAt else dates.simpleDateObj(timeNow=True),
        tracks=tracks,
        coverImage=coverImage
    )

    return album

# SPOTIFY SEARCH BY ALBUM NAME RESPONSE

# {
#     "albums": {
#         "href": "https://api.spotify.com/v1/search?offset=0&limit=1&query=Watch%20the%20Throme&type=album",
#         "limit": 1,
#         "next": "https://api.spotify.com/v1/search?offset=1&limit=1&query=Watch%20the%20Throme&type=album",
#         "offset": 0,
#         "previous": None,
#         "total": 800,
#         "items": [
#             {
#                 "album_type": "album",
#                 "total_tracks": 12,
#                 "external_urls": {
#                     "spotify": "https://open.spotify.com/album/0OcMap99vLEeGkBCfCwRwS"
#                 },
#                 "href": "https://api.spotify.com/v1/albums/0OcMap99vLEeGkBCfCwRwS",
#                 "id": "0OcMap99vLEeGkBCfCwRwS",
#                 "images": [
#                     {
#                         "height": 640,
#                         "url": "https://i.scdn.co/image/ab67616d0000b27352e61456aa4995ba48d94e30",
#                         "width": 640,
#                     },
#                     {
#                         "height": 300,
#                         "url": "https://i.scdn.co/image/ab67616d00001e0252e61456aa4995ba48d94e30",
#                         "width": 300,
#                     },
#                     {
#                         "height": 64,
#                         "url": "https://i.scdn.co/image/ab67616d0000485152e61456aa4995ba48d94e30",
#                         "width": 64,
#                     },
#                 ],
#                 "name": "Watch The Throne",
#                 "release_date": "2011-08-08",
#                 "release_date_precision": "day",
#                 "type": "album",
#                 "uri": "spotify:album:0OcMap99vLEeGkBCfCwRwS",
#                 "artists": [
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/3nFkdlSjzX9mRTtwJOzDYB"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/3nFkdlSjzX9mRTtwJOzDYB",
#                         "id": "3nFkdlSjzX9mRTtwJOzDYB",
#                         "name": "JAY-Z",
#                         "type": "artist",
#                         "uri": "spotify:artist:3nFkdlSjzX9mRTtwJOzDYB",
#                     },
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/5K4W6rqBFWDnAN6FQUkS6x"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/5K4W6rqBFWDnAN6FQUkS6x",
#                         "id": "5K4W6rqBFWDnAN6FQUkS6x",
#                         "name": "Kanye West",
#                         "type": "artist",
#                         "uri": "spotify:artist:5K4W6rqBFWDnAN6FQUkS6x",
#                     },
#                 ],
#             }
#         ],
#     }
# }


# SPOTIFY DETAILS BY ALBUM ID RESPONSE

# {
#     "album_type": "album",
#     "total_tracks": 12,
#     "available_markets": [
#         "AR",
#         "AU",
#         "AT",
#         "BE",
#         "BO",
#         "BR",
#         "BG",
#         "CA",
#         "CL",
#         "CO",
#         "CR",
#         "CY",
#         "CZ",
#         "DK",
#         "DO",
#         "DE",
#         "EC",
#         "EE",
#         "SV",
#         "FI",
#         "FR",
#         "GR",
#         "GT",
#         "HN",
#         "HK",
#         "HU",
#         "IS",
#         "IE",
#         "IT",
#         "LV",
#         "LT",
#         "LU",
#         "MY",
#         "MT",
#         "MX",
#         "NL",
#         "NZ",
#         "NI",
#         "NO",
#         "PA",
#         "PY",
#         "PE",
#         "PH",
#         "PL",
#         "PT",
#         "SG",
#         "SK",
#         "ES",
#         "SE",
#         "CH",
#         "TW",
#         "TR",
#         "UY",
#         "US",
#         "GB",
#         "AD",
#         "LI",
#         "MC",
#         "ID",
#         "JP",
#         "TH",
#         "VN",
#         "RO",
#         "IL",
#         "ZA",
#         "SA",
#         "AE",
#         "BH",
#         "QA",
#         "OM",
#         "KW",
#         "EG",
#         "MA",
#         "DZ",
#         "TN",
#         "LB",
#         "JO",
#         "PS",
#         "IN",
#         "BY",
#         "KZ",
#         "MD",
#         "UA",
#         "AL",
#         "BA",
#         "HR",
#         "ME",
#         "MK",
#         "RS",
#         "SI",
#         "KR",
#         "BD",
#         "PK",
#         "LK",
#         "GH",
#         "KE",
#         "NG",
#         "TZ",
#         "UG",
#         "AG",
#         "AM",
#         "BS",
#         "BB",
#         "BZ",
#         "BT",
#         "BW",
#         "BF",
#         "CV",
#         "CW",
#         "DM",
#         "FJ",
#         "GM",
#         "GE",
#         "GD",
#         "GW",
#         "GY",
#         "HT",
#         "JM",
#         "KI",
#         "LS",
#         "LR",
#         "MW",
#         "MV",
#         "ML",
#         "MH",
#         "FM",
#         "NA",
#         "NR",
#         "NE",
#         "PW",
#         "PG",
#         "WS",
#         "SM",
#         "ST",
#         "SN",
#         "SC",
#         "SL",
#         "SB",
#         "KN",
#         "LC",
#         "VC",
#         "SR",
#         "TL",
#         "TO",
#         "TT",
#         "TV",
#         "VU",
#         "AZ",
#         "BN",
#         "BI",
#         "KH",
#         "CM",
#         "TD",
#         "KM",
#         "GQ",
#         "SZ",
#         "GA",
#         "GN",
#         "KG",
#         "LA",
#         "MO",
#         "MR",
#         "MN",
#         "NP",
#         "RW",
#         "TG",
#         "UZ",
#         "ZW",
#         "BJ",
#         "MG",
#         "MU",
#         "MZ",
#         "AO",
#         "CI",
#         "DJ",
#         "ZM",
#         "CD",
#         "CG",
#         "IQ",
#         "LY",
#         "TJ",
#         "VE",
#         "ET",
#         "XK",
#     ],
#     "external_urls": {
#         "spotify": "https://open.spotify.com/album/0OcMap99vLEeGkBCfCwRwS"
#     },
#     "href": "https://api.spotify.com/v1/albums/0OcMap99vLEeGkBCfCwRwS",
#     "id": "0OcMap99vLEeGkBCfCwRwS",
#     "images": [
#         {
#             "url": "https://i.scdn.co/image/ab67616d0000b27352e61456aa4995ba48d94e30",
#             "height": 640,
#             "width": 640,
#         },
#         {
#             "url": "https://i.scdn.co/image/ab67616d00001e0252e61456aa4995ba48d94e30",
#             "height": 300,
#             "width": 300,
#         },
#         {
#             "url": "https://i.scdn.co/image/ab67616d0000485152e61456aa4995ba48d94e30",
#             "height": 64,
#             "width": 64,
#         },
#     ],
#     "name": "Watch The Throne",
#     "release_date": "2011-08-08",
#     "release_date_precision": "day",
#     "type": "album",
#     "uri": "spotify:album:0OcMap99vLEeGkBCfCwRwS",
#     "artists": [
#         {
#             "external_urls": {
#                 "spotify": "https://open.spotify.com/artist/3nFkdlSjzX9mRTtwJOzDYB"
#             },
#             "href": "https://api.spotify.com/v1/artists/3nFkdlSjzX9mRTtwJOzDYB",
#             "id": "3nFkdlSjzX9mRTtwJOzDYB",
#             "name": "JAY-Z",
#             "type": "artist",
#             "uri": "spotify:artist:3nFkdlSjzX9mRTtwJOzDYB",
#         },
#         {
#             "external_urls": {
#                 "spotify": "https://open.spotify.com/artist/5K4W6rqBFWDnAN6FQUkS6x"
#             },
#             "href": "https://api.spotify.com/v1/artists/5K4W6rqBFWDnAN6FQUkS6x",
#             "id": "5K4W6rqBFWDnAN6FQUkS6x",
#             "name": "Kanye West",
#             "type": "artist",
#             "uri": "spotify:artist:5K4W6rqBFWDnAN6FQUkS6x",
#         },
#     ],
#     "tracks": {
#         "href": "https://api.spotify.com/v1/albums/0OcMap99vLEeGkBCfCwRwS/tracks?offset=0&limit=50",
#         "limit": 50,
#         "next": None,
#         "offset": 0,
#         "previous": None,
#         "total": 12,
#         "items": [
#             {
#                 "artists": [
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/3nFkdlSjzX9mRTtwJOzDYB"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/3nFkdlSjzX9mRTtwJOzDYB",
#                         "id": "3nFkdlSjzX9mRTtwJOzDYB",
#                         "name": "JAY-Z",
#                         "type": "artist",
#                         "uri": "spotify:artist:3nFkdlSjzX9mRTtwJOzDYB",
#                     },
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/5K4W6rqBFWDnAN6FQUkS6x"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/5K4W6rqBFWDnAN6FQUkS6x",
#                         "id": "5K4W6rqBFWDnAN6FQUkS6x",
#                         "name": "Kanye West",
#                         "type": "artist",
#                         "uri": "spotify:artist:5K4W6rqBFWDnAN6FQUkS6x",
#                     },
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/2h93pZq0e7k5yf4dywlkpM"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/2h93pZq0e7k5yf4dywlkpM",
#                         "id": "2h93pZq0e7k5yf4dywlkpM",
#                         "name": "Frank Ocean",
#                         "type": "artist",
#                         "uri": "spotify:artist:2h93pZq0e7k5yf4dywlkpM",
#                     },
#                     {
#                         "external_urls": {
#                             "spotify": "https://open.spotify.com/artist/1W3FSF1BLpY3hlVIgvenLz"
#                         },
#                         "href": "https://api.spotify.com/v1/artists/1W3FSF1BLpY3hlVIgvenLz",
#                         "id": "1W3FSF1BLpY3hlVIgvenLz",
#                         "name": "The-Dream",
#                         "type": "artist",
#                         "uri": "spotify:artist:1W3FSF1BLpY3hlVIgvenLz",
#                     },
#                 ],
#                 "available_markets": [
#                     "AR",
#                     "AU",
#                     "AT",
#                     "BE",
#                     "BO",
#                     "BR",
#                     "BG",
#                     "CA",
#                     "CL",
#                     "CO",
#                     "CR",
#                     "CY",
#                     "CZ",
#                     "DK",
#                     "DO",
#                     "DE",
#                     "EC",
#                     "EE",
#                     "SV",
#                     "FI",
#                     "FR",
#                     "GR",
#                     "GT",
#                     "HN",
#                     "HK",
#                     "HU",
#                     "IS",
#                     "IE",
#                     "IT",
#                     "LV",
#                     "LT",
#                     "LU",
#                     "MY",
#                     "MT",
#                     "MX",
#                     "NL",
#                     "NZ",
#                     "NI",
#                     "NO",
#                     "PA",
#                     "PY",
#                     "PE",
#                     "PH",
#                     "PL",
#                     "PT",
#                     "SG",
#                     "SK",
#                     "ES",
#                     "SE",
#                     "CH",
#                     "TW",
#                     "TR",
#                     "UY",
#                     "US",
#                     "GB",
#                     "AD",
#                     "LI",
#                     "MC",
#                     "ID",
#                     "JP",
#                     "TH",
#                     "VN",
#                     "RO",
#                     "IL",
#                     "ZA",
#                     "SA",
#                     "AE",
#                     "BH",
#                     "QA",
#                     "OM",
#                     "KW",
#                     "EG",
#                     "MA",
#                     "DZ",
#                     "TN",
#                     "LB",
#                     "JO",
#                     "PS",
#                     "IN",
#                     "BY",
#                     "KZ",
#                     "MD",
#                     "UA",
#                     "AL",
#                     "BA",
#                     "HR",
#                     "ME",
#                     "MK",
#                     "RS",
#                     "SI",
#                     "KR",
#                     "BD",
#                     "PK",
#                     "LK",
#                     "GH",
#                     "KE",
#                     "NG",
#                     "TZ",
#                     "UG",
#                     "AG",
#                     "AM",
#                     "BS",
#                     "BB",
#                     "BZ",
#                     "BT",
#                     "BW",
#                     "BF",
#                     "CV",
#                     "CW",
#                     "DM",
#                     "FJ",
#                     "GM",
#                     "GE",
#                     "GD",
#                     "GW",
#                     "GY",
#                     "HT",
#                     "JM",
#                     "KI",
#                     "LS",
#                     "LR",
#                     "MW",
#                     "MV",
#                     "ML",
#                     "MH",
#                     "FM",
#                     "NA",
#                     "NR",
#                     "NE",
#                     "PW",
#                     "PG",
#                     "WS",
#                     "SM",
#                     "ST",
#                     "SN",
#                     "SC",
#                     "SL",
#                     "SB",
#                     "KN",
#                     "LC",
#                     "VC",
#                     "SR",
#                     "TL",
#                     "TO",
#                     "TT",
#                     "TV",
#                     "VU",
#                     "AZ",
#                     "BN",
#                     "BI",
#                     "KH",
#                     "CM",
#                     "TD",
#                     "KM",
#                     "GQ",
#                     "SZ",
#                     "GA",
#                     "GN",
#                     "KG",
#                     "LA",
#                     "MO",
#                     "MR",
#                     "MN",
#                     "NP",
#                     "RW",
#                     "TG",
#                     "UZ",
#                     "ZW",
#                     "BJ",
#                     "MG",
#                     "MU",
#                     "MZ",
#                     "AO",
#                     "CI",
#                     "DJ",
#                     "ZM",
#                     "CD",
#                     "CG",
#                     "IQ",
#                     "LY",
#                     "TJ",
#                     "VE",
#                     "ET",
#                     "XK",
#                 ],
#                 "disc_number": 1,
#                 "duration_ms": 272506,
#                 "explicit": True,
#                 "external_urls": {
#                     "spotify": "https://open.spotify.com/track/7r6PigmGzlB3YPB7wvBBbi"
#                 },
#                 "href": "https://api.spotify.com/v1/tracks/7r6PigmGzlB3YPB7wvBBbi",
#                 "id": "7r6PigmGzlB3YPB7wvBBbi",
#                 "name": "No Church In The Wild",
#                 "preview_url": None,
#                 "track_number": 1,
#                 "type": "track",
#                 "uri": "spotify:track:7r6PigmGzlB3YPB7wvBBbi",
#                 "is_local": False,
#             }
#         ],
#     },
#     "copyrights": [
#         {"text": "© 2011 Roc-A-Fella Records, LLC/Shawn Carter", "type": "C"},
#         {"text": "℗ 2011 Roc-A-Fella Records, LLC/Shawn Carter", "type": "P"},
#     ],
#     "external_ids": {"upc": "00602527809076"},
#     "genres": [],
#     "label": "Roc Nation/RocAFella/IDJ",
#     "popularity": 74,
# }
