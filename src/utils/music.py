import discord
import os
from datetime import datetime
from uuid import uuid4
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.utils import dates
from src.utils import images

from src.classes import EmbedReply

from src import constants

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
        rating: float = None,
        favourite: bool = False,
        comments: str = None,
        album: "Album" = None
    ):
        self.spotifyID = spotifyID
        self.name = name
        self.artists = artists
        self.explicit = explicit
        self.link = link
        self.trackNumber = trackNumber
        self.durationMS = durationMS
        self.rating = rating
        self.favourite = favourite
        self.comments = comments
        self.album = album

    def setRating(self, rating: float) -> None:
        self.rating = rating

        return

    def getArtists(self, formatted: bool = False) -> Artist | str:
        if formatted:
            return ", ".join([artist.name for artist in self.artists])
        else:
            return self.artists
        
    def setComments(self, comments: str | None):
        self.comments = comments

    def parseComments(self, formatted: bool = False):
        if formatted:
            return "(No Comments)" if not self.comments else self.comments
        else:
            return self.comments
        
    def markFavourite(self, state: bool):
        self.favourite = state

    def getRating(self, formatted: bool = False, roundedTo: int = 2) -> float:
        if self.rating == None and formatted:
            return "Unrated"
        elif (self.rating >= 0) and (self.rating <= self.album.ratingOutOf):
            if formatted and roundedTo != None:
                return f"{round(self.rating, abs(roundedTo))}/{self.album.ratingOutOf}"
            elif formatted and roundedTo == None:
                return f"{self.rating}/{self.album.ratingOutOf}"
            elif not formatted and roundedTo != None:
                return round(self.rating, abs(roundedTo))
            else:
                return self.rating
        elif self.rating == -1 and formatted:
            return "Skipped"
        else:
            return self.rating
    
    async def rateTrack(self, ctx: discord.ApplicationContext):
        rateTrackEmbed = TrackRatingEmbedReply(
            self
        )

        return await rateTrackEmbed.send(ctx, ephemeral=True)

class TrackRatingEmbedReply(EmbedReply):
    def __init__(self, track: Track):
        formattedArtists: str = track.getArtists(True)
        
        title = f"♦️ {track.trackNumber}/{track.album.totalTracks()} 👤 {formattedArtists} ⏯️ {track.name} 🔗↗️"
        super().__init__(title, "albumratings", url=track.album.link, description="Assign a rating to, favourite, or skip rating the song using the buttons/box below.")

        self.set_thumbnail(url=track.album.coverImage)
        self.colour = track.album.coverImageColour
        self.set_footer(text=f"Song data provided by Spotify®. Rating ID: {track.album.ratingID}", icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png")

        self.add_field(name="***Previous Rating***", value=f"`{track.getRating(True)}`", inline=True)
        self.add_field(name="***Comments***", value=track.parseComments(True), inline=True)

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
        ratingOutOf: int | float = constants.RATINGS_OUT_OF,
        coverImage: str = None,
        coverImageColour: str = None,
        comments: str = None
    ):
        self.ratingID = uuid4().hex
        self.spotifyID = spotifyID
        self.name = name
        self.artists = artists
        self.link = link
        self.releaseDate = releaseDate
        self.createdBy = createdBy
        self.createdAt = createdAt
        self.editedAt = editedAt
        self.tracks = tracks
        self.ratingOutOf = ratingOutOf
        self.coverImage = coverImage
        self.coverImageColour = coverImageColour
        self.comments = comments

    def totalTracks(self) -> int:
        return len(self.tracks)

    def meanRating(self, formatted: bool = False) -> float:
        if not self.tracks:
            raise Exception("There are no tracks assigned to the album so there is no average rating!")
        
        cleanedRatingList: list[float] = []

        for track in self.tracks:
            if track.rating == None and formatted:
                return "Unfinished"
            elif track.rating == None and not formatted:
                raise ValueError("There is an unrated song in the album rating and an average could not be calculated! Please finish the rating.")
            elif (track.rating >= 0) and (track.rating <= constants.RATINGS_OUT_OF):
                cleanedRatingList.append(track.rating)
            elif track.rating == -1:
                continue
            else:
                raise Exception(f"Shits broken! Rating condition unaccounted for: {track.rating} on rating {self.ratingID}.")
        
        mean = round(sum(cleanedRatingList) / len(cleanedRatingList), 1)

        if formatted:
            return f"{mean}/{self.ratingOutOf}"

        return mean
    
    def serializeRating(self) -> bytes:
        serialized = pickle.dumps(self)

        return serialized
    
    def addTrack(self, track: Track):
        track.album = self

        self.tracks.append(track)

    def getArtists(self, formatted: bool = False) -> Artist | str:
        if formatted:
            return ", ".join([artist.name for artist in self.artists])
        else:
            return self.artists
    
    def setComments(self, comments: str | None):
        self.comments = comments
    
    def parseComments(self, formatted: bool = False):
        if formatted:
            return "(No Comments)" if not self.comments else self.comments
        else:
            return self.comments
    
    def releaseYear(self, formatted: bool = False, includeMonth: bool = False) -> int | str | None:
        if not self.releaseDate and formatted:
            return "N/D"
        elif not self.releaseDate and not formatted:
            return None
        elif self.releaseDate:
            if includeMonth:
                return f"{self.releaseDate.strftime("%B")}, {self.releaseDate.year}"
            else:
                return self.releaseDate.year
        else:
            raise Exception(f"releaseYear: Invalid release year! Rating ID: {self.ratingID}")

class AlbumRatingEmbedReply(EmbedReply):
    def __init__(self, album: Album):
        formattedArtists: str = album.getArtists(True)

        title = f"👤 {formattedArtists} 💿 {album.name} 📅 {album.releaseYear(True, True)} 🔗↗️"
        super().__init__(title, "albumratings", url=album.link, description="")

        self.set_thumbnail(url=album.coverImage)
        self.colour = album.coverImageColour
        self.set_footer(text=f"Album data provided by Spotify®. Rating ID: {album.ratingID}", icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png")

        for track in album.tracks:
            self.description += f"**{track.trackNumber}.** {track.name} · `{track.getRating(True)}`\n"


        self.add_field(name="***Overall Rating***", value=album.meanRating(True), inline=True)
        self.add_field(name="***Rating By***", value=f"<@{album.createdBy}>", inline=True)
        self.add_field(name="***Rated On***", value=f"{dates.formatSimpleDate(album.createdAt)}", inline=True)

        self.add_field(name="***Comments***", value=album.parseComments(True), inline=False)

class EditCommentModal(discord.ui.Modal):
    def __init__(self, obj: Album | Track, *args, **kwargs) -> None:
        super().__init__(title=f"Comments · {obj.name}", *args, **kwargs)

        self.obj = obj

        self.add_item(
            discord.ui.InputText(
                label="Edit Comments",
                max_length=1000,
                value=obj.parseComments()
            )
        )
    
    async def callback(self, ctx: discord.Interaction):
        if not self.children[0].value:
            self.obj.setComments(None)
        else:
            self.obj.setComments(self.children[0].value)

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

def parseAlbumDetails(data: dict, createdBy: int, createdAt: datetime = None, comments: str = None, ratingOutOf = constants.RATINGS_OUT_OF) -> Album:
    if not data:
        raise ValueError("No data provided to album parser.")
    
    spotifyID = data["id"]
    name = data["name"]
    artists = [Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"]) for artist in data["artists"]]
    link = data["external_urls"]["spotify"]
    releaseDate = dates.simpleDateObj(data["release_date"])

    coverImage = None if not data["images"] else data["images"][0]["url"]

    coverImageColour = None

    if coverImage:
        coverImageColour = discord.Colour.from_rgb(*(int(i) for i in images.extractColours(coverImage)[0]))

    album = Album(
        spotifyID,
        name,
        artists,
        link,
        releaseDate,
        createdBy,
        createdAt if createdAt else dates.simpleDateObj(timeNow=True),
        ratingOutOf=ratingOutOf,
        coverImage=coverImage,
        coverImageColour=coverImageColour,
        comments=comments
    )

    for trackData in data["tracks"]["items"]:
        trackArtists = [Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"]) for artist in trackData["artists"]]

        track = Track(
            trackData["id"],
            trackData["name"],
            trackArtists,
            trackData["explicit"],
            trackData["external_urls"]["spotify"],
            trackData["track_number"],
            trackData["duration_ms"]
        )
        
        album.addTrack(track)

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
