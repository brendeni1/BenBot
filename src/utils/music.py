import discord
import os
from datetime import datetime
from uuid import uuid4
import pickle
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from src.utils import dates
from src.utils import images
from src.utils import text

from src.classes import EmbedReply, OpenLink

from src import constants

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Timeouts in mins.
TIMEOUT_TO_PICK_ALBUM = 1 * (60)
TIMEOUT_FOR_RATING_SELECT = 300 * (60)

FAVOURITE_INDEX_OPTIONS = sorted([
    1,
    2,
    3,
])

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


class CancelButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(label="Cancel Rating", style=discord.ButtonStyle.danger, emoji="⛔", **kwargs)

    async def callback(self, ctx: discord.ApplicationContext):
        self.view.disable_all_items()
        self.view.cancelled = True
        self.view.stop()

        reply = EmbedReply(
            "Album Rating - Cancelled",
            "albumratings",
            True,
            description="Album rating cancelled.",
        )

        await ctx.response.edit_message(view=self.view, embed=reply)


class SaveRatingButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Finish Rating", style=discord.ButtonStyle.success, emoji="💾", **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        self.view.disable_all_items()
        self.view.stop()

        reply = EmbedReply(
            "Album Rating - Saved", "albumratings", description="Album rating saved. ✅"
        )

        await ctx.response.edit_message(view=self.view, embed=reply)

class NextTrackButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Next Track", style=discord.ButtonStyle.primary, emoji="➡️", **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view
        view.index += 1
        if view.index >= len(view.album.tracks):
            await view.finish()
        else:
            await view.showTrackAndRating(ctx)


class PreviousTrackButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Previous Track", style=discord.ButtonStyle.primary, emoji="⬅️", **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view
        if view.index > 0:
            view.index -= 1
            await view.showTrackAndRating(ctx)

class SongRatingView(discord.ui.View):
    def __init__(self, album: "Album", startIndex: int = 0):
        super().__init__(timeout=TIMEOUT_FOR_RATING_SELECT, disable_on_timeout=True)

        self.album = album
        self.index = startIndex
        self.cancelled = False
        self.message: discord.Message | None = None

        self._updateItems()

    def _updateItems(self):
        self.clear_items()

        track = self.album.tracks[self.index]
        trackAmount = len(self.album.tracks)

        isFirstSong: bool = self.index > 0
        isLastSong: bool = self.index == len(self.album.tracks) - 1

        self.add_item(SelectSongRating(track, row=0))

        if trackAmount > 1:
            currentFavouriteIndex = track.getFavouriteIndex()

            for indexOption in FAVOURITE_INDEX_OPTIONS:
                if (currentFavouriteIndex == indexOption) or (trackAmount < indexOption):
                    self.add_item(FavouriteButton(indexOption, track, row=1, disabled=True))

                    continue

                self.add_item(FavouriteButton(indexOption, track, row=1))
            
            hasRating: bool = currentFavouriteIndex in FAVOURITE_INDEX_OPTIONS
            self.add_item(ClearFavouriteButton(track, row=1, disabled=not hasRating))

            self.add_item(PreviousTrackButton(row=2, disabled=not isFirstSong))
            self.add_item(NextTrackButton(row=2, disabled=isLastSong))
        
        self.add_item(SaveRatingButton(row=2))
        self.add_item(OpenLink("Play Song On Spotify", track.link, row=2))
        
        self.add_item(CancelButton(row=3))

    async def showTrackAndRating(self, ctx: discord.Interaction):
        track = self.album.tracks[self.index]

        wholeAlbumEmbed = AlbumRatingEmbedReply(self.album)
        songRatingEmbed = TrackRatingEmbedReply(track)

        self._updateItems()

        await ctx.response.edit_message(
            embeds=[wholeAlbumEmbed, songRatingEmbed], view=self
        )

    async def on_timeout(self):
        self.disable_all_items()

        reply = EmbedReply(
            "Album Rating - Timed Out",
            "albumratings",
            True,
            description=f"Album rating timed out after {round((TIMEOUT_FOR_RATING_SELECT/60)/60, 2)} hrs of inactivity. Please retry the rating.",
        )

        if self.message:
            await self.message.edit(embed=reply, view=self)


class SelectSongRating(discord.ui.Select):
    def __init__(self, track: "Track", **kwargs):
        self.track = track

        scale = list(
            text.frange(
                0,
                track.album.ratingOutOf + constants.RATINGS_STEP,
                constants.RATINGS_STEP,
            )
        )

        super().__init__(
            placeholder=f"Choose Rating ({scale[0]}-{scale[-1]})",
            options=[
                discord.SelectOption(
                    label=f"{i}/{track.album.ratingOutOf}",
                    default=track.getRating(roundedTo=None) == i,
                    value=str(i),
                )
                for i in scale
            ],
            **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        self.track.setRating(float(self.values[0]))

        await view.showTrackAndRating(ctx)

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
        favouriteIndex: int | None = None,
        comments: str = None,
        album: "Album" = None,
    ):
        self.spotifyID = spotifyID
        self.name = name
        self.artists = artists
        self.explicit = explicit
        self.link = link
        self.trackNumber = trackNumber
        self.durationMS = durationMS
        self.rating = rating
        self.favouriteIndex = favouriteIndex
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
            return "*(No Comments)*" if not self.comments else self.comments
        else:
            return self.comments

    def setFavouriteIndex(self, idx: int | None):
        self.favouriteIndex = idx

    def getFavouriteIndex(self) -> int | None:
        return self.favouriteIndex

    def getRating(self, formatted: bool = False, roundedTo: int = 2) -> float:
        if self.rating == None and formatted:
            return "Unrated"
        elif (
            (self.rating != None)
            and (self.rating >= 0)
            and (self.rating <= self.album.ratingOutOf)
        ):
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

class FavouriteButton(discord.ui.Button):
    def __init__(self, ranking: int, track: Track, **kwargs):
        self.track = track
        self.ranking = ranking

        medal = constants.RANKING_MEDALS[str(ranking)] if str(ranking) in constants.RANKING_MEDALS else None
        
        ordinized = text.ordinal(ranking)

        super().__init__(
            label=f"{ordinized} Place", style=discord.ButtonStyle.secondary, emoji=medal, **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        for track in view.album.tracks:
            if track.getFavouriteIndex() == self.ranking:
                track.setFavouriteIndex(None)
        
        self.track.setFavouriteIndex(self.ranking)
        
        await view.showTrackAndRating(ctx)

class ClearFavouriteButton(discord.ui.Button):
    def __init__(self, track: Track, **kwargs):
        self.track = track

        super().__init__(
            label=f"Unfavourite", style=discord.ButtonStyle.secondary, emoji="🗑️", **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        self.track.setFavouriteIndex(None)
        
        await view.showTrackAndRating(ctx)

class TrackRatingEmbedReply(EmbedReply):
    def __init__(self, track: Track):
        formattedArtists: str = track.getArtists(True)

        title = f"({track.trackNumber}/{track.album.totalTracks()})  👤 {formattedArtists} ⏯️ {track.name} 🔗↗️"
        super().__init__(
            title,
            "albumratings",
            url=track.album.link + "?=discordIsBroken=True",
            description="Assign rating/comment, or favourite/ignore the song using the buttons/box below. Move through the tracklist using the Next/Previous buttons, and when all songs are rated, save the rating using the Finish Rating button.",
        )

        self.set_thumbnail(url=track.album.coverImage)
        self.colour = track.album.coverImageColour
        self.set_footer(
            text=f"Song data provided by Spotify®. Rating ID: {track.album.ratingID}",
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png",
        )

        favouriteIndex = track.getFavouriteIndex()

        medalFormatted = f"{constants.RANKING_MEDALS[str(favouriteIndex)]} {text.ordinal(favouriteIndex)} Place" if favouriteIndex in FAVOURITE_INDEX_OPTIONS else "*(Not Favourited)*"

        self.add_field(
            name="***Favourite Rating***", value=medalFormatted, inline=True
        )

        self.add_field(
            name="***Song Comments***", value=track.parseComments(True), inline=True
        )

        self.set_author(
            name=track.album.createdBy.global_name,
            icon_url=track.album.createdBy.avatar.url,
        )


class Album:
    def __init__(
        self,
        spotifyID: str,
        name: str,
        artists: list[Artist],
        link: str,
        releaseDate: datetime,
        createdBy: discord.Member,
        createdAt: datetime = dates.simpleDateObj(timeNow=True),
        editedAt: datetime = None,
        tracks: list[Track] | None = None,
        ratingOutOf: int | float = constants.RATINGS_OUT_OF,
        coverImage: str = None,
        coverImageColour: str = None,
        comments: str = None,
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
        self.tracks = tracks if tracks is not None else []
        self.ratingOutOf = ratingOutOf
        self.coverImage = coverImage
        self.coverImageColour = coverImageColour
        self.comments = comments

    def totalTracks(self) -> int:
        return len(self.tracks)

    def meanRating(self, formatted: bool = False) -> float:
        if not self.tracks:
            raise Exception(
                "There are no tracks assigned to the album so there is no average rating!"
            )

        cleanedRatingList: list[float] = []

        for track in self.tracks:
            if track.rating == None and formatted:
                return "Unfinished"
            elif track.rating == None and not formatted:
                raise ValueError(
                    "There is an unrated song in the album rating and an average could not be calculated! Please finish the rating."
                )
            elif (track.rating >= 0) and (track.rating <= self.ratingOutOf):
                cleanedRatingList.append(track.rating)
            elif track.rating == -1:
                continue
            else:
                raise Exception(
                    f"Shits broken! Rating condition unaccounted for: {track.rating} on rating {self.ratingID}."
                )

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
            return "*(No Comments)*" if not self.comments else self.comments
        else:
            return self.comments

    def releaseYear(
        self, formatted: bool = False, includeMonth: bool = False
    ) -> int | str | None:
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
            raise Exception(
                f"releaseYear: Invalid release year! Rating ID: {self.ratingID}"
            )


class AlbumRatingEmbedReply(EmbedReply):
    def __init__(self, album: Album):
        formattedArtists: str = album.getArtists(True)

        title = f"👤 {formattedArtists} 💿 {album.name} 📅 {album.releaseYear(True, True)} 🔗↗️"
        super().__init__(title, "albumratings", url=album.link, description="")

        self.set_thumbnail(url=album.coverImage)
        self.colour = album.coverImageColour
        self.set_footer(
            text=f"Album data provided by Spotify®. Rating ID: {album.ratingID}",
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png",
        )

        for track in album.tracks:
            favouriteIndex = track.getFavouriteIndex()

            if not favouriteIndex:
                self.description += (
                    f"**{track.trackNumber}.** {track.name} · `{track.getRating(True)}`\n"
                )
            else:
                medal = constants.RANKING_MEDALS[str(favouriteIndex)] if str(favouriteIndex) in constants.RANKING_MEDALS else f"({text.ordinal(favouriteIndex)} Place)"
                
                self.description += (
                    f"**{track.trackNumber}.** {medal} {track.name} · `{track.getRating(True)}`\n"
                )

        self.add_field(
            name="***Overall Album Rating***",
            value=f"`{album.meanRating(True)}`",
            inline=True,
        )
        self.add_field(
            name="***Album Rating By***", value=album.createdBy.mention, inline=True
        )
        self.add_field(
            name="***Album Rated On***",
            value=f"{dates.formatSimpleDate(album.createdAt)}",
            inline=True,
        )

        self.add_field(
            name="***Album Comments***", value=album.parseComments(True), inline=False
        )

        self.set_author(
            name=album.createdBy.global_name, icon_url=album.createdBy.avatar.url
        )


class EditCommentModal(discord.ui.Modal):
    def __init__(self, obj: Album | Track, *args, **kwargs) -> None:
        super().__init__(title=f"Comments · {obj.name}", *args, **kwargs)

        self.obj = obj

        self.add_item(
            discord.ui.InputText(
                label="Edit Comments", max_length=1000, value=obj.parseComments()
            )
        )

    async def callback(self, ctx: discord.Interaction):
        if not self.children[0].value:
            self.obj.setComments(None)
        else:
            self.obj.setComments(self.children[0].value)


class SelectAlbum(discord.ui.Select):
    def __init__(self, choices: list[tuple]):
        super().__init__(
            placeholder="Choose an album...",
            options=[
                discord.SelectOption(
                    label=f"{choice[1]} · {choice[3]}",
                    description=choice[2],
                    emoji=text.numberToEmoji(choice[0] + 1),
                    value=choice[4],
                )
                for choice in choices
            ],
            row=0
        )

    async def callback(self, ctx: discord.Interaction):
        self.view.choice = self.values[0]

        self.view.disable_all_items()
        self.view.stop()
        await ctx.response.edit_message(view=self.view)

        await ctx.delete_original_response()


class EditCommentsButton(discord.ui.Button):
    def __init__(self, obj: Album | Track, **kwargs):
        super().__init__(
            label="Edit Comment", style=discord.ButtonStyle.primary, emoji="💬", **kwargs
        )

        self.obj = obj

    async def callback(self, ctx: discord.ApplicationContext):
        self.view.disable_all_items()
        self.view.stop()


class ChooseAlbumView(discord.ui.View):
    def __init__(self, choices: list[tuple]):
        super().__init__(timeout=TIMEOUT_TO_PICK_ALBUM, disable_on_timeout=True)

        self.choice = None

        self.add_item(SelectAlbum(choices))
        self.add_item(CancelButton())

    async def on_timeout(self):
        self.disable_all_items()

        reply = EmbedReply(
            "Album Rating - Timed Out",
            "albumratings",
            True,
            description="Album rating timed out. Please retry.",
        )

        if self.message:
            await self.message.edit(embed=reply, view=self)


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


def parseAlbumDetails(
    data: dict,
    createdBy: discord.Member,
    createdAt: datetime = None,
    comments: str = None,
    ratingOutOf=constants.RATINGS_OUT_OF,
) -> Album:
    if not data:
        raise ValueError("No data provided to album parser.")

    spotifyID = data["id"]
    name = data["name"]
    artists = [
        Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"])
        for artist in data["artists"]
    ]
    link = data["external_urls"]["spotify"]
    releaseDate = dates.simpleDateObj(data["release_date"])

    coverImage = None if not data["images"] else data["images"][0]["url"]

    coverImageColour = None

    if coverImage:
        coverImageColour = discord.Colour.from_rgb(
            *(int(i) for i in images.extractColours(coverImage)[0])
        )

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
        comments=comments,
    )

    for trackData in data["tracks"]["items"]:
        trackArtists = [
            Artist(artist["id"], artist["name"], artist["external_urls"]["spotify"])
            for artist in trackData["artists"]
        ]

        track = Track(
            trackData["id"],
            trackData["name"],
            trackArtists,
            trackData["explicit"],
            trackData["external_urls"]["spotify"],
            trackData["track_number"],
            trackData["duration_ms"],
        )

        album.addTrack(track)

    return album
