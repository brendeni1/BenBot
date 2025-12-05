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

from src.cogs.albumratings import AlbumRatings

from src.classes import *

from src import constants

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Timeouts in mins.
TIMEOUT_TO_PICK_ALBUM = 1 * (60)
TIMEOUT_FOR_RATING_SELECT = 300 * (60)
TIMEOUT_FOR_DUPE_RATING_CONFIRMATION = 5 * (60)

FAVOURITE_INDEX_OPTIONS = sorted(
    [
        1,
        2,
        3,
    ]
)

COMMENT_LENGTH_CHARACTER_LIMIT = 1000
COMMENT_LENGTH_CHARACTER_LIMIT_IN_EMBED = 200

FAST_NAV_SKIP_AMOUNT = 3


class Artist:
    def __init__(self, spotifyID: str, name: str, link: str):
        self.spotifyID = spotifyID
        self.name = name
        self.link = link


class EditRatingButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Edit Rating",
            style=discord.ButtonStyle.secondary,
            emoji="✏️",
            custom_id="edit_rating",
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        footer = embed.footer.text or ""
        ratingID = footer.split("Rating ID: ")[-1] if "Rating ID:" in footer else None

        if not ratingID:
            reply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                True,
                description="Could not determine Rating ID for this message.",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)
            return

        db = LocalDatabase()
        result = db.get("SELECT * FROM albumRatings WHERE ratingID = ?", (ratingID,))

        if not result:
            reply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                True,
                description="Rating not found in database.",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)
            return

        createdByID = result[0][1]
        if (interaction.user.id != createdByID) and not (
            await interaction.client.is_owner(interaction.user)
        ):
            reply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                True,
                description="You cannot edit someone else's rating!",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)
            return

        cog: AlbumRatings = interaction.client.get_cog("AlbumRatings")
        if not cog:
            reply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                True,
                description="No album rating cog to run command!",
            )

            await interaction.response.send_message(embed=reply)
            return

        reply = EmbedReply(
            "Album Ratings - Edit Rating", "albumratings", description="Editor opened."
        )

        replyMessage = await interaction.response.send_message(
            embed=reply, ephemeral=True
        )
        await replyMessage.delete_original_response()

        await cog._albumrating_edit_core(
            user=interaction.user,
            ratingID=ratingID,
            channel=interaction.channel,
            guild=interaction.guild,
            bot=interaction.client,
        )


class DeleteRatingButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Delete Rating",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            custom_id="delete_rating",
            **kwargs,
        )

    async def callback(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        footer = embed.footer.text or ""
        ratingID = footer.split("Rating ID: ")[-1] if "Rating ID:" in footer else None

        if not ratingID:
            reply = EmbedReply(
                "Album Ratings - Delete Rating",
                "albumratings",
                True,
                description="Could not determine Rating ID for this message.",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)
            return

        database = LocalDatabase()
        result = database.get(
            "SELECT * FROM albumRatings WHERE ratingID = ?", (ratingID,)
        )

        if not result:
            reply = EmbedReply(
                "Album Ratings - Delete Rating",
                "albumratings",
                True,
                description="Rating not found in database. You can safely delete the message.",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)
            return

        result = SmallRating(result[0])

        createdByID = result.createdBy
        if (interaction.user.id != createdByID) and not (
            await interaction.client.is_owner(interaction.user)
        ):
            reply = EmbedReply(
                "Album Ratings - Delete Rating",
                "albumratings",
                True,
                description="You cannot delete someone else's rating!",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)

            return

        confirmationReply = EmbedReply(
            "Album Ratings - Delete Rating",
            "albumratings",
            description=f"Are you sure you want to delete the following rating?",
        )

        confirmationReply.add_field(
            name=text.truncateString(
                f"{result.ratingAlbum} · {result.ratingArtist}", 256
            )[0],
            value=f"ID: {result.ratingID}",
        )

        confirmationReplyView = DeleteRatingView()

        deleteResponse = await interaction.response.send_message(
            embed=confirmationReply, view=confirmationReplyView, ephemeral=True
        )

        timedOut = await confirmationReplyView.wait()

        try:
            if timedOut:
                reply = EmbedReply(
                    "Album Ratings - Delete Rating",
                    "albumratings",
                    True,
                    description="You ran out of time to delete the rating. Please try again.",
                )

                await deleteResponse.edit_original_response(embed=reply, view=None)

                return

            if not confirmationReplyView.confirmDelete:
                await deleteResponse.delete_original_response()

                return

            await interaction.message.delete()

            database.setOne("DELETE FROM albumRatings WHERE ratingID = ?", (ratingID,))

            reply = EmbedReply(
                "Album Ratings - Deleted",
                "albumratings",
                description=f"Successfully deleted rating. ✅",
            )

            reply.add_field(
                name=text.truncateString(
                    f"{result.ratingAlbum} · {result.ratingArtist}", 256
                )[0],
                value=f"ID: {result.ratingID}",
            )

            await deleteResponse.edit_original_response(embed=reply, view=None)
        except discord.errors.NotFound:
            pass


class FinishedRatingPersistentMessageButtonsView(discord.ui.View):
    def __init__(self, albumLink: str | None = None):
        super().__init__(timeout=None)

        self.add_item(DeleteRatingButton(row=0))
        self.add_item(EditRatingButton(row=0))

        # Only add link button if we have a link
        if albumLink:
            self.add_item(OpenLink("Open Album on Spotify", albumLink, row=1))


class DeleteRatingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.confirmDelete: bool = False

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancelButton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):

        self.stop()

        await interaction.response.defer()

    @discord.ui.button(
        label="Delete Rating", style=discord.ButtonStyle.danger, emoji="🗑️"
    )
    async def deleteButton(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ):
        self.confirmDelete = True

        self.stop()

        await interaction.response.defer()


class CancelConfirmView(discord.ui.View):
    def __init__(self, ratingView: "SongRatingView", embeds: list[discord.Embed]):
        self.ratingView = ratingView
        self.embeds = embeds

        super().__init__(timeout=30)

    @discord.ui.button(label="Go Back", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def deny(self, button: discord.ui.Button, ctx: discord.Interaction):
        await ctx.response.edit_message(embeds=self.embeds, view=self.ratingView)

        self.stop()

    @discord.ui.button(
        label="Cancel Rating", style=discord.ButtonStyle.danger, emoji="⛔"
    )
    async def confirm(self, button: discord.ui.Button, ctx: discord.Interaction):
        response = await ctx.response.defer()

        await ctx.delete_original_response()

        self.ratingView.cancelled = True

        self.stop()


class CancelButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Cancel Rating",
            style=discord.ButtonStyle.danger,
            emoji="⛔",
            **kwargs,
        )

    async def callback(self, ctx: discord.ApplicationContext):
        cancelEmbed = EmbedReply(
            "Album Rating - Confirm Cancel",
            "albumratings",
            description="Are you sure you want to cancel the album rating?",
        )

        await ctx.response.edit_message(
            embed=cancelEmbed, view=CancelConfirmView(self.view, ctx.message.embeds)
        )


class DuplicateRatingConfirmationView(discord.ui.View):
    def __init__(self, originalUser: discord.User):
        self.userAcknowledged = False
        self.originalUser = originalUser
        self.paginator = None

        super().__init__(timeout=TIMEOUT_FOR_DUPE_RATING_CONFIRMATION)

    # 1. Helper function to check permissions and send your custom error
    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.originalUser.id:
            return True

        # If not the owner, send the error message
        reply = EmbedReply(
            "Album Ratings - Duplicates Found",
            "albumratings",
            True,
            description="You cannot decide that for someone else!",
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)
        return False

    @discord.ui.button(label="Cancel Rating", style=discord.ButtonStyle.red, emoji="⛔")
    async def cancelCallback(self, button, interaction):
        # 2. Call the check at the start of the button callback
        if not await self.check_permissions(interaction):
            return

        self.stop()

        if self.paginator:
            self.paginator.stop()

        await interaction.response.defer()

    @discord.ui.button(
        label="Continue Rating", style=discord.ButtonStyle.green, emoji="➡️"
    )
    async def continueCallback(self, button, interaction):
        # 3. Call the check at the start of the button callback
        if not await self.check_permissions(interaction):
            return

        self.userAcknowledged = True

        self.stop()

        if self.paginator:
            self.paginator.stop()

        await interaction.response.defer()


class SaveRatingButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Finish Rating",
            style=discord.ButtonStyle.success,
            emoji="💾",
            **kwargs,
        )

    async def callback(self, ctx: discord.Interaction):
        self.view.disable_all_items()
        self.view.stop()

        await ctx.response.defer()


class NextTrackButton(discord.ui.Button):
    def __init__(self, **kwargs):
        super().__init__(
            label="Next Track", style=discord.ButtonStyle.primary, emoji="➡️", **kwargs
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view
        view.index += 1
        if view.index >= view.album.totalTracks():
            await view.finish()
        else:
            await view.showTrackAndRating(ctx)


class AlbumNavigationButton(discord.ui.Button):
    def __init__(self, skipAmount: int, **kwargs):
        super().__init__(
            **kwargs,
        )

        self.skipAmount = skipAmount

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        if not self.skipAmount:
            raise ValueError("Skip amount not positive or negative.")
        elif self.skipAmount > 0:
            newIndex = min(view.album.totalTracks() - 1, view.index + self.skipAmount)
        else:
            newIndex = max(0, view.index + self.skipAmount)

        view.index = newIndex

        await self.view.showTrackAndRating(ctx)


class SongRatingView(discord.ui.View):
    def __init__(self, album: "Album", startIndex: int = 0):
        super().__init__(timeout=TIMEOUT_FOR_RATING_SELECT, disable_on_timeout=True)

        self.album = album
        self.index = startIndex
        self.cancelled = False
        self.message: discord.Message | None = None

        self._updateItems()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the rating owner can interact."""
        if (interaction.user.id != self.album.createdBy.id) and (
            interaction.user.id != int(os.environ.get("OWNER"))
        ):
            reply = EmbedReply(
                "Album Ratings - Create Rating",
                "albumratings",
                True,
                description="You can’t edit someone else’s rating.",
            )

            await interaction.response.send_message(embed=reply, ephemeral=True)

            return False
        return True

    def _updateItems(self):
        self.clear_items()

        track: Track = self.album.tracks[self.index]
        trackAmount = self.album.totalTracks()

        isFirstSong: bool = self.index == 0
        isLastSong: bool = self.index == trackAmount - 1

        self.add_item(SelectSongRating(track, row=0))

        if trackAmount > 1:
            currentFavouriteIndex = track.getFavouriteIndex()

            for indexOption in FAVOURITE_INDEX_OPTIONS:
                self.add_item(
                    FavouriteButton(
                        indexOption,
                        track,
                        row=1,
                        disabled=(currentFavouriteIndex == indexOption)
                        or (trackAmount < indexOption)
                        or track.getRating() == -1,
                    )
                )

            hasRating: bool = currentFavouriteIndex in FAVOURITE_INDEX_OPTIONS
            self.add_item(ClearFavouriteButton(track, row=1, disabled=not hasRating))

            self.add_item(
                ExcludeFromRatingButton(
                    track,
                    row=2,
                    disabled=any(
                        [
                            track.getRating() == -1,
                            all(
                                [
                                    trackReLoop.getRating() == -1
                                    for trackReLoop in self.album.tracks
                                    if trackReLoop != track
                                ]
                            ),
                        ]
                    ),
                )
            )

        self.add_item(EditCommentsButton("Song Comments", track, row=2))

        self.add_item(EditCommentsButton("Album Comments", self.album, row=2))

        self.add_item(CustomAlbumCoverButton(self.album, row=2))

        self.add_item(
            AlbumNavigationButton(
                -FAST_NAV_SKIP_AMOUNT,
                label=f"Back {FAST_NAV_SKIP_AMOUNT}",
                emoji="⏪",
                style=discord.ButtonStyle.primary,
                row=3,
                disabled=isFirstSong,
            )
        )
        self.add_item(
            AlbumNavigationButton(
                -1,
                label="Back",
                emoji="⬅️",
                style=discord.ButtonStyle.primary,
                row=3,
                disabled=isFirstSong,
            )
        )
        self.add_item(
            AlbumNavigationButton(
                1,
                label="Forward",
                emoji="➡️",
                style=discord.ButtonStyle.primary,
                row=3,
                disabled=isLastSong,
            )
        )
        self.add_item(
            AlbumNavigationButton(
                FAST_NAV_SKIP_AMOUNT,
                label=f"Forward {FAST_NAV_SKIP_AMOUNT}",
                emoji="⏩",
                style=discord.ButtonStyle.primary,
                row=3,
                disabled=isLastSong,
            )
        )
        # self.add_item(OpenLink("Play Song On Spotify", track.link, row=3))

        self.add_item(CancelButton(row=4))
        self.add_item(SaveRatingButton(row=4))

    async def showTrackAndRating(self, ctx: discord.Interaction):
        track = self.album.tracks[self.index]

        wholeAlbumEmbed = AlbumRatingEmbedReply(self.album)
        songRatingEmbed = TrackRatingEmbedReply(track)

        self._updateItems()

        try:
            await ctx.response.edit_message(
                embeds=[wholeAlbumEmbed, songRatingEmbed], view=self
            )
        except discord.NotFound:
            print(
                "random fuckass error in SongRatingView again where the edit bugs (notfound) but nothing actually is broken?"
            )

            pass  # idek bruh

    async def on_timeout(self):
        reply = EmbedReply(
            "Album Rating - Timed Out",
            "albumratings",
            True,
            description=f"Album rating timed out after {round((TIMEOUT_FOR_RATING_SELECT/60)/60, 2)} hrs of inactivity. Please retry the rating.",
        )

        try:
            await self.message.edit(embed=reply, view=None)
        except discord.NotFound:
            pass  # message already deleted/edited elsewhere

        self.stop()


class SelectSongRating(discord.ui.Select):
    def __init__(self, track: "Track", **kwargs):
        self.track = track

        scale = [
            text.smartRound(i)
            for i in text.frange(
                0,
                track.album.ratingOutOf + constants.RATINGS_STEP,
                constants.RATINGS_STEP,
            )
        ]

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
            **kwargs,
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
        discNumber: int,
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
        self.discNumber = discNumber
        self.durationMS = durationMS
        self.rating = rating
        self.favouriteIndex = favouriteIndex
        self.comments = comments
        self.album = album

    def getDuration(self, formatted: bool = False) -> int | str:
        if formatted:
            convertedToSeconds = round(self.durationMS / 1000)

            formattedToHuman = dates.formatSeconds(convertedToSeconds)

            return formattedToHuman
        else:
            return self.durationMS

    def getTrackNumber(self, relativeToDisk: bool = False) -> int:
        if relativeToDisk:
            return self.trackNumber

        trackNumber = self.album.tracks.index(self, start=1)

        return trackNumber

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

    def parseComments(
        self, formatted: bool = False, overrideCommentTruncate: int = 350
    ):
        if formatted:
            return (
                "*(No Comments)*"
                if not self.comments
                else text.truncateString(self.comments, overrideCommentTruncate)[0]
            )
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
                return f"{text.smartRound(self.rating, abs(roundedTo))}/{self.album.ratingOutOf}"
            elif formatted and roundedTo == None:
                return f"{self.rating}/{self.album.ratingOutOf}"
            elif not formatted and roundedTo != None:
                return text.smartRound(self.rating, abs(roundedTo))
            else:
                return self.rating
        elif self.rating == -1 and formatted:
            return "Excluded"
        else:
            return self.rating


class FavouriteButton(discord.ui.Button):
    def __init__(self, ranking: int, track: Track, **kwargs):
        self.track = track
        self.ranking = ranking

        medal = (
            constants.RANKING_MEDALS[str(ranking)]
            if str(ranking) in constants.RANKING_MEDALS
            else None
        )

        ordinized = text.ordinal(ranking)

        super().__init__(
            label=f"{ordinized} Place",
            style=discord.ButtonStyle.secondary,
            emoji=medal,
            **kwargs,
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        for track in view.album.tracks:
            if track.getFavouriteIndex() == self.ranking:
                track.setFavouriteIndex(None)

        self.track.setFavouriteIndex(self.ranking)

        await view.showTrackAndRating(ctx)


class ExcludeFromRatingButton(discord.ui.Button):
    def __init__(self, track: Track, **kwargs):
        self.track = track

        super().__init__(
            label=f"Exclude Song",
            style=discord.ButtonStyle.secondary,
            emoji="↪️",
            **kwargs,
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        self.track.setRating(-1)
        self.track.setFavouriteIndex(None)

        await view.showTrackAndRating(ctx)


class ClearFavouriteButton(discord.ui.Button):
    def __init__(self, track: Track, **kwargs):
        self.track = track

        super().__init__(
            label=f"Unfavourite",
            style=discord.ButtonStyle.secondary,
            emoji="🗑️",
            **kwargs,
        )

    async def callback(self, ctx: discord.Interaction):
        view: SongRatingView = self.view

        self.track.setFavouriteIndex(None)

        await view.showTrackAndRating(ctx)


class TrackRatingEmbedReply(EmbedReply):
    def __init__(self, track: Track):
        formattedArtists: str = track.getArtists(True)

        positionString = ""

        allDiscs: list[int] = track.album.getAllDiscNumbers()

        if len(allDiscs) > 1:
            positionString = f"Disc {track.discNumber}/{len(allDiscs)} · Track {track.trackNumber}/{len(track.album.getTracksOnDisc(track.discNumber))} ({track.album.totalTracks()} Total)"
        else:
            positionString = f"Track {track.trackNumber}/{track.album.totalTracks()}"

        title = text.truncateString(
            f"{positionString} 👤 {formattedArtists} ⏯️ {track.name}{' (🔞) ' if track.explicit else ' '}🔗↗️",
            256,
        )[0]
        super().__init__(
            title,
            "albumratings",
            url=track.album.link + "?=discordIsBroken=True",
            description="Assign rating/comment, or favourite/exclude the song using the buttons/box below; move through the tracklist using the Next/Previous buttons. When all songs are rated, save using the Finish Rating button.",
        )

        self.set_thumbnail(url=track.album.getCoverImage())
        self.colour = track.album.coverImageColour
        self.set_footer(
            text=f"Song data provided by Spotify®. Rating ID: {track.album.ratingID}",
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png",
        )

        favouriteIndex = track.getFavouriteIndex()

        medalFormatted = (
            f"{constants.RANKING_MEDALS[str(favouriteIndex)]} {text.ordinal(favouriteIndex)} Place"
            if favouriteIndex in FAVOURITE_INDEX_OPTIONS
            else "*(Not Favourited)*"
        )

        if track.album.totalTracks() > 1:
            self.add_field(
                name="***Favourite Rating***", value=medalFormatted, inline=True
            )

        self.add_field(
            name="***Song Duration***", value=track.getDuration(True), inline=True
        )

        self.add_field(
            name="***Song Comments***", value=track.parseComments(True), inline=False
        )

        self.set_author(
            name=track.album.createdBy.global_name,
            icon_url=track.album.createdBy.avatar.url,
        )


class SmallRating:
    def __init__(self, result: tuple):
        self.ratingID = result[0]
        self.createdBy = result[1]
        self.createdAt = result[2]
        self.editedAt = result[3]
        self.ratingArtist = result[4]
        self.ratingAlbum = result[5]
        self.spotifyAlbumID = result[6]
        self.formattedRating = result[7]
        self.trackAmount = result[8]
        self.lastRelatedMessage = result[9]
        self.serializedRating = result[10]


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
        editedAt: datetime | None = None,
        tracks: list[Track] | None = None,
        ratingOutOf: int | float | None = constants.RATINGS_OUT_OF,
        coverImage: str | None = None,
        customCoverImage: str | None = None,
        coverImageColour: str | None = None,
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
        self.customCoverImage = customCoverImage
        self.coverImageColour = coverImageColour
        self.comments = comments

    def albumDuration(self, formatted: bool = False) -> int | str:
        """
        Returns the album duration in milliseconds.
        """
        durationCounter = 0

        for track in self.tracks:
            durationCounter += track.durationMS

        if formatted:
            convertedToSeconds = round(durationCounter / 1000)

            formattedToHuman = dates.formatSeconds(convertedToSeconds)

            return formattedToHuman
        else:
            return durationCounter

    def totalTracks(self, includeSkipped: bool = True) -> int:
        if not includeSkipped:
            filteredTracks = [track for track in self.tracks if track.getRating() != -1]

            return len(filteredTracks)

        return len(self.tracks)

    def getAllDiscNumbers(self) -> list[int]:
        if not self.tracks:
            raise ValueError(
                "There are no tracks for this album and the discs could not be processed."
            )

        discs = []

        for track in self.tracks:
            if track.discNumber in discs:
                continue

            discs.append(track.discNumber)

        discs.sort()

        return discs

    def getTracksOnDisc(self, targetDisc: int) -> list[Track]:
        if targetDisc not in self.getAllDiscNumbers():
            raise ValueError("gettracksondisc: Disc index out of range!")

        filteredTracks: list[Track] = [
            track for track in self.tracks if track.discNumber == targetDisc
        ]

        return filteredTracks

    def updateEditedTime(self) -> datetime:
        timestamp = dates.simpleDateObj(timeNow=True)

        self.editedAt = timestamp

        return timestamp

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

        mean = text.smartRound(sum(cleanedRatingList) / len(cleanedRatingList), 1)

        if formatted:
            return f"{mean}/{self.ratingOutOf}"

        return mean

    def packAlbumRating(self, lastRelatedMessage: discord.Message) -> SmallRating:
        ratingID: str = self.ratingID

        createdBy: int = self.createdBy.id

        createdAt: str = dates.formatSimpleDate(
            self.createdAt, formatString="%Y-%m-%d %H:%M:%S"
        )
        editedAt: str | None = (
            dates.formatSimpleDate(self.editedAt, formatString="%Y-%m-%d %H:%M:%S")
            if self.editedAt
            else None
        )

        ratingArtist: str = self.getArtists(True)
        ratingAlbum: str = self.name
        ratingAlbumSpotifyID: str = self.spotifyID
        formattedRating: str = self.meanRating(True)
        trackAmount: int = len(self.tracks)

        lastRelatedMessage = lastRelatedMessage.id

        self.createdBy = self.createdBy.id
        serializedRating = pickle.dumps(self)

        tupRtg = (
            ratingID,
            createdBy,
            createdAt,
            editedAt,
            ratingArtist,
            ratingAlbum,
            ratingAlbumSpotifyID,
            formattedRating,
            trackAmount,
            lastRelatedMessage,
            serializedRating,
        )

        return SmallRating(tupRtg)

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

    def getCoverImage(self, *, includeCustom: bool = True) -> str:
        return (
            self.customCoverImage
            if self.customCoverImage and includeCustom
            else self.coverImage
        )

    def setCoverImage(self, *, url: str | None = None, custom: bool = False):
        if url:
            if custom:
                self.customCoverImage = url
            else:
                self.coverImage = url
        else:
            self.customCoverImage = None

        self.coverImageColour = discord.Colour.from_rgb(
            *(int(i) for i in images.extractColours(self.getCoverImage())[0])
        )

    def parseComments(
        self, formatted: bool = False, overrideCommentTruncate: int = 2000
    ):
        if formatted:
            return (
                "*(No Comments)*"
                if not self.comments
                else text.truncateString(self.comments, overrideCommentTruncate)[0]
            )
        else:
            return self.comments

    def formatReleaseDate(
        self, formatted: bool = False, verbose: bool = False
    ) -> int | str | None:
        """
        Returns the album's release year. Set verbose to get the full date.
        """
        if not self.releaseDate and formatted:
            return "N/D"
        elif not self.releaseDate and not formatted:
            return None
        elif self.releaseDate:
            if verbose:
                return dates.formatSimpleDate(
                    self.releaseDate, includeTime=False, relativity=False
                )
            else:
                return self.releaseDate.year
        else:
            raise Exception(
                f"formatReleaseDate: Invalid release date! Rating ID: {self.ratingID}"
            )


class EditCommentsButton(discord.ui.Button):
    def __init__(self, label: str, obj: Album | Track, **kwargs):
        self.obj = obj

        super().__init__(
            label=label, style=discord.ButtonStyle.secondary, emoji="💬", **kwargs
        )

    async def callback(self, ctx: discord.ApplicationContext):
        await ctx.response.send_modal(EditCommentsModal(self.obj, self.view))


class CustomAlbumCoverButton(discord.ui.Button):
    def __init__(self, obj: Album, **kwargs):
        self.obj = obj

        super().__init__(
            label="Override Cover Art",
            style=discord.ButtonStyle.secondary,
            emoji="🖼️",
            **kwargs,
        )

    async def callback(self, ctx: discord.ApplicationContext):
        await ctx.response.send_modal(CustomAlbumCoverModal(self.obj, self.view))


class AlbumRatingEmbedReply(EmbedReply):
    def __init__(self, album: Album | list[Album]):
        isAveraged = isinstance(album, list)

        targetAlbumDetails: Album = album[0] if isAveraged else album

        formattedArtists: str = targetAlbumDetails.getArtists(True)

        title = text.truncateString(
            f"👤 {formattedArtists} 💽 {targetAlbumDetails.name} 📅 {targetAlbumDetails.formatReleaseDate(True, True)} 🔗↗️",
            256,
        )[0]
        super().__init__(
            title, "albumratings", url=targetAlbumDetails.link, description=""
        )

        self.set_thumbnail(url=targetAlbumDetails.getCoverImage())
        self.colour = targetAlbumDetails.coverImageColour
        self.set_footer(
            text=f"Album data provided by Spotify®."
            + ("" if isAveraged else f" Rating ID: {targetAlbumDetails.ratingID}"),
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png",
        )

        seenDiscs = set()

        allDiscs: list[int] = targetAlbumDetails.getAllDiscNumbers()

        for track in targetAlbumDetails.tracks:
            if isAveraged:
                formattedDetailsBelowTrack = ""
                ratings = []

                for rating in album:
                    currentSelectedTrackObject = list(
                        filter(lambda i: i.spotifyID == track.spotifyID, rating.tracks)
                    )

                    if not currentSelectedTrackObject:
                        continue

                    currentSelectedTrackObject = currentSelectedTrackObject[0]

                    songRating = currentSelectedTrackObject.getRating()

                    if songRating != None and (songRating != -1):
                        ratings.append(songRating)

                    ratingFormatted = currentSelectedTrackObject.getRating(True)

                    formattedDetailsBelowTrack += f"\n\u00a0\u00a0\u00a0\u00a0⤷ {rating.createdBy.mention}'s Rating: {ratingFormatted}"

                    comments = currentSelectedTrackObject.parseComments()

                    formattedDetailsBelowTrack += (
                        f"\n\u00a0\u00a0\u00a0\u00a0⤷ {rating.createdBy.mention} 💬 {text.truncateString(comments, COMMENT_LENGTH_CHARACTER_LIMIT_IN_EMBED / 2)[0]}"
                        if comments
                        else ""
                    )

                discString = ""

                if len(allDiscs) > 1 and (track.discNumber not in seenDiscs):
                    discString = f"{'' if track.discNumber == 1 else '\u00a0'}\n***💿 Disc {track.discNumber}***\n"

                    seenDiscs.add(track.discNumber)

                if not ratings:
                    averageSongRatingAcrossAll = "All Ratings Excluded/Unfinished"
                else:
                    averageSongRatingAcrossAll = f"{text.smartRound(sum(ratings) / len(ratings))}/{targetAlbumDetails.ratingOutOf}"

                self.description += f"{discString}**{track.trackNumber}.** {track.name} · `{averageSongRatingAcrossAll}`{formattedDetailsBelowTrack}\n"
            else:
                favouriteIndex = track.getFavouriteIndex()

                medal = (
                    f" {constants.RANKING_MEDALS[str(favouriteIndex)] if str(favouriteIndex) in constants.RANKING_MEDALS else f'({text.ordinal(favouriteIndex)} Place)'} "
                    if favouriteIndex
                    else " "
                )

                comments = track.parseComments()

                formattedComments = (
                    f"\n\u00a0\u00a0\u00a0\u00a0⤷ 💬 {text.truncateString(comments, COMMENT_LENGTH_CHARACTER_LIMIT_IN_EMBED)[0]}"
                    if comments
                    else ""
                )

                discString = ""

                if len(allDiscs) > 1 and (track.discNumber not in seenDiscs):
                    discString = f"{'' if track.discNumber == 1 else '\u00a0'}\n***💿 Disc {track.discNumber}***\n"

                    seenDiscs.add(track.discNumber)

                self.description += f"{discString}**{track.trackNumber}.**{medal}{track.name} · `{track.getRating(True)}`{formattedComments}\n"

        if isAveraged:
            formattedRatedBy = ""
            formattedRatedOn = ""
            formattedComments = ""
            individualRatingBreakdown = ""
            ratings = []

            for rating in album:
                try:
                    meanRating = rating.meanRating()

                    ratings.append(meanRating)
                except ValueError:
                    pass

                individualRatingBreakdown += (
                    f"`{rating.meanRating(True)}` ({rating.createdBy.mention})\n"
                )
                formattedRatedBy += (
                    f"{rating.createdBy.mention} ({rating.meanRating(True)})\n"
                )
                formattedRatedOn += f"{dates.formatSimpleDate(rating.createdAt, discordDateFormat="f")} ({rating.createdBy.mention})\n"
                formattedComments += f'\n"{rating.parseComments(True, 350)}" - {rating.createdBy.mention}\n\u00a0'

            if not ratings:
                averageAlbumRatingOfAll = "All Ratings Unfinished"
            else:
                averageAlbumRatingOfAll = f"{text.smartRound(sum(ratings) / len(ratings))}/{targetAlbumDetails.ratingOutOf}"

            self.add_field(
                name="***Average Album Rating of All***",
                value=f"`{averageAlbumRatingOfAll}`\n{individualRatingBreakdown}",
                inline=True,
            )
            self.add_field(
                name="***Album Ratings By***", value=formattedRatedBy, inline=True
            )
            self.add_field(
                name="***Album Ratings On***", value=formattedRatedOn, inline=True
            )
            self.add_field(
                name="***Album Duration***",
                value=f"{targetAlbumDetails.albumDuration(True)}",
                inline=False,
            )
            self.add_field(
                name="***Album Comments***", value=formattedComments, inline=False
            )

        if not isAveraged:
            self.add_field(
                name="***Overall Album Rating***",
                value=f"`{targetAlbumDetails.meanRating(True)}`",
                inline=True,
            )

        if not isAveraged:
            self.add_field(
                name="***Album Duration***",
                value=f"{targetAlbumDetails.albumDuration(True)}",
                inline=True,
            )

        if not isAveraged:
            self.add_field(
                name="***Album Rating By***",
                value=targetAlbumDetails.createdBy.mention,
                inline=True,
            )

        if not isAveraged:
            self.add_field(
                name="***Album Rated On***",
                value=f"{dates.formatSimpleDate(targetAlbumDetails.createdAt, discordDateFormat="f")}",
                inline=True,
            )

        if targetAlbumDetails.editedAt and not isAveraged:
            self.add_field(
                name="***Rating Edited***",
                value=f"{dates.formatSimpleDate(targetAlbumDetails.editedAt, discordDateFormat="f")}",
                inline=True,
            )

        if not isAveraged:
            self.add_field(
                name="***Album Comments***",
                value=targetAlbumDetails.parseComments(True),
                inline=False,
            )

        if not isAveraged:
            self.set_author(
                name=targetAlbumDetails.createdBy.global_name
                or targetAlbumDetails.createdBy.name,
                icon_url=targetAlbumDetails.createdBy.avatar.url,
            )


class EditCommentsModal(discord.ui.Modal):
    def __init__(
        self, obj: Album | Track, view: SongRatingView, *args, **kwargs
    ) -> None:
        self.obj = obj
        self.view = view

        super().__init__(
            title=text.truncateString(f"Comments On {obj.name}", 45)[0], *args, **kwargs
        )

        self.add_item(
            discord.ui.InputText(
                style=discord.InputTextStyle.paragraph,
                label="Edit Comments",
                max_length=COMMENT_LENGTH_CHARACTER_LIMIT,
                value=obj.parseComments(),
                required=False,
            )
        )

    async def callback(self, ctx: discord.Interaction):
        if not self.children[0].value:
            self.obj.setComments(None)
        else:
            self.obj.setComments(self.children[0].value)

        await self.view.showTrackAndRating(ctx)


class CustomAlbumCoverModal(discord.ui.Modal):
    def __init__(self, obj: Album, view: SongRatingView, *args, **kwargs) -> None:
        self.obj = obj
        self.view = view

        super().__init__(
            title=text.truncateString(f"Custom Cover For {obj.name}", 45)[0],
            *args,
            **kwargs,
        )

        self.add_item(
            discord.ui.InputText(
                style=discord.InputTextStyle.short,
                label="Direct URL to Image (Leave Blank to Reset)",
                value=obj.customCoverImage,
                required=False,
            )
        )

    async def callback(self, ctx: discord.Interaction):
        url = self.children[0].value

        if url:
            isImage = images.urlIsImage(url)

            if not isImage:
                errorEmbed = EmbedReply(
                    "Album Ratings - Override Cover Art - Error",
                    "albumratings",
                    error=True,
                    description="You supplied an invalid link; an image could not be found.\n\nPlease ensure that the link leads directly to an image.",
                )

                await ctx.response.send_message(embed=errorEmbed, ephemeral=True)

                return

        self.obj.setCoverImage(url=url, custom=True)

        await self.view.showTrackAndRating(ctx)


class SelectAlbum(discord.ui.Select):
    def __init__(self, choices: dict):
        super().__init__(
            placeholder="Choose an album...",
            options=[
                discord.SelectOption(
                    label=text.truncateString(
                        f"{choice['name']} · {choice['releaseDate']} ({choice['trackAmount']} Track{'s' if choice['trackAmount'] > 1 else ''})",
                        100,
                    )[0],
                    description=text.truncateString(choice["artists"], 100)[0],
                    emoji=text.numberToEmoji(
                        choice["index"] + 1, emojiIfSingleDigitsOnly="ℹ️"
                    ),
                    value=choice["spotifyID"],
                )
                for choice in choices
            ],
            row=0,
        )

    async def callback(self, ctx: discord.Interaction):
        self.view.choice = self.values[0]

        self.view.disable_all_items()
        self.view.stop()

        await ctx.response.defer()


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

        try:
            if self.message:
                await self.message.edit(embed=reply, view=None)
        except discord.NotFound:
            pass  # message already deleted/edited elsewhere


def searchForAlbumName(query: str, limit=5, type="album") -> list:
    if not query:
        raise ValueError("utils > music.py > albumQuery: Album query is blank!")

    spotifyClient = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
        )
    )

    albumResults = spotifyClient.search(q=query, limit=limit, type=type)

    return albumResults


def fetchAlbumDetailsByID(albumID: str) -> dict:
    if not albumID:
        raise ValueError("utils > music.py > albumDetails: Album ID is blank!")

    spotifyClient = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
        )
    )

    albumResults = spotifyClient.album(album_id=albumID)

    return albumResults


def parseAlbumDetails(
    data: dict,
    createdBy: discord.Member,
    trackLimit: int,
    *,
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

    coverImageURL = None if not data["images"] else data["images"][0]["url"]

    album = Album(
        spotifyID,
        name,
        artists,
        link,
        releaseDate,
        createdBy,
        createdAt if createdAt else dates.simpleDateObj(timeNow=True),
        ratingOutOf=ratingOutOf,
        comments=comments,
    )

    album.setCoverImage(url=coverImageURL)

    rawTracks: list[dict] = data["tracks"]["items"][:trackLimit]

    for trackData in rawTracks:
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
            trackData["disc_number"],
            trackData["duration_ms"],
        )

        album.addTrack(track)

    return album


def unpackAlbumRating(bot: discord.Bot, packedAlbumRating: bytes) -> Album:
    unserializedAlbumRating: Album = pickle.loads(packedAlbumRating)

    unserializedAlbumRating.createdBy = bot.get_user(unserializedAlbumRating.createdBy)

    return unserializedAlbumRating


def sortByRating(result: SmallRating) -> float:
    rawRating: str = result.formattedRating.split("/")

    score, outOf = float(rawRating[0]), float(rawRating[1])

    return score / outOf
