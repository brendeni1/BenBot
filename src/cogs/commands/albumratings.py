import posixpath

import discord
from pyparsing import results
import requests
import asyncio
import sys
from discord.ext import commands, pages
import urllib
from src.errors import *

from src.classes import *
from src.utils import music
from src.utils import dates

RATING_CHANNEL = 946507420916678688

LIST_RATINGS_PER_PAGE = 7

DELETE_SAVED_REPLY_AFTER = 15

ALBUM_APISEARCH_RESULTS_LIMIT = 5

SLEEP_BETWEEN_API_ATTEMPTS = 2

SINGLE_ALBUM_TRACK_CRITERIA = 1

DUPLICATE_RATING_TIMEOUT_DELETEAFTER = 30

TIMEOUT_VIEW_RATINGS_PAGINATOR = 14 * (60)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _error_reply(title: str, e: Exception) -> EmbedReply:
    """Build a standard error EmbedReply."""
    return EmbedReply(title, "albumratings", True, description=str(e))


async def paginateRatingList(
    results,
    bot: discord.Bot,
    title: str,
    description: str,
    *,
    showUserInResults: bool = False,
    showRatingInResults: bool = True,
) -> list[discord.Embed]:
    pageList = []

    ratingChannel = bot.get_channel(RATING_CHANNEL)
    guild_id = None
    if ratingChannel and hasattr(ratingChannel, "guild") and ratingChannel.guild:
        guild_id = ratingChannel.guild.id

    if not guild_id:
        print("Could not retrieve Guild ID for URL construction.")

    for chunk in range(0, len(results), LIST_RATINGS_PER_PAGE):
        page = EmbedReply(title, "albumratings", description=description)

        for rating in results[chunk : chunk + LIST_RATINGS_PER_PAGE]:
            formattedCreatedAt = dates.formatSimpleDate(
                rating.createdAt, discordDateFormat="d"
            )

            albumTitleTruncated = text.truncateString(rating.ratingAlbum, 70)[0]

            formattedRatingName = text.truncateString(
                f"{albumTitleTruncated} · {rating.ratingArtist} · {formattedCreatedAt}",
                256,
            )[0]

            descriptor = ""

            if showRatingInResults:
                descriptor += f"\nRating: {rating.formattedRating}"

            descriptor += f"\nRating ID: {rating.ratingID}"

            if showUserInResults:
                descriptor += f"\nRating By: <@{rating.createdBy}>"

            oldMessageID = rating.lastRelatedMessage

            if guild_id and oldMessageID:
                jump_url = f"https://discord.com/channels/{guild_id}/{RATING_CHANNEL}/{oldMessageID}"
                descriptor += f"\nView: {jump_url}"

            page.add_field(name=formattedRatingName, value=descriptor, inline=False)

        pageList.append(page)

    return pageList


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class AlbumRatings(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot
        self.description = "Album rating commands."

    albumRatings = discord.SlashCommandGroup(
        "albumrating",
        "Use these commands to add, edit, and delete album ratings.",
        guild_ids=[799341195109203998],
    )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _fetch_and_authorize_rating(
        self,
        rating_id: str,
        invoking_user: discord.User,
    ) -> tuple["LocalDatabase", "music.SmallRating"]:
        """
        Fetch a rating row from the DB and verify the invoking user owns it
        (or is a bot owner). Returns (database, SmallRating) on success,
        raises Exception on failure.
        """
        database = LocalDatabase(database="albumratings")

        row = database.get("SELECT * FROM ratings WHERE ratingID = ?", (rating_id,))

        if not row:
            raise Exception(
                "There were no ratings with that ID found!\n\n"
                "Try using the list command to narrow down your search."
            )

        rating = music.SmallRating(row[0])

        if (rating.createdBy != invoking_user.id) and not (
            await self.bot.is_owner(invoking_user)
        ):
            raise Exception(
                f"That's not your rating!\n\n"
                f"To see a list of your ratings, use: "
                f"`/albumrating list member member:@{invoking_user.name}`"
            )

        return database, rating

    async def _publish_rating_message(
        self,
        channel: discord.TextChannel,
        embed: discord.Embed,
        album_link: str,
        old_message_id: int | None,
        *,
        edit_in_place: bool = True,
    ) -> tuple[discord.Message, str]:
        """
        Send or update the public rating message in *channel*.

        If *edit_in_place* is True and the old message still exists, it is
        edited rather than replaced. Otherwise the old message (if found) is
        deleted and a new one is sent.

        Returns (message, warning_text) where warning_text is non-empty only
        when the original message was missing and edit_in_place was requested.
        """
        persistent_view = music.FinishedRatingPersistentMessageButtonsView(album_link)
        old_ref: discord.Message | None = None
        warning = ""

        if old_message_id:
            try:
                old_ref = await channel.fetch_message(old_message_id)
            except discord.errors.NotFound:
                if edit_in_place:
                    warning = (
                        "\n\n⚠️WARN: The original message tied to this rating could not "
                        "be found and edit_original_rating_message was set to True when "
                        "this command was invoked. Instead of editing the message, a new "
                        "one was sent and can be found through the link above."
                    )

        if edit_in_place and old_ref and not warning:
            message = await old_ref.edit(embed=embed, view=persistent_view)
        else:
            if old_ref:
                await old_ref.delete()
            message = await channel.send(embed=embed, view=persistent_view)

        return message, warning

    async def _respond_with_rating_list(
        self,
        ctx: discord.ApplicationContext,
        results: list,
        title: str,
        description: str,
        *,
        showUserInResults: bool = False,
        showRatingInResults: bool = True,
    ) -> None:
        """Build a paginated rating list and send it to the interaction."""
        page_list = await paginateRatingList(
            results,
            self.bot,
            title,
            description,
            showUserInResults=showUserInResults,
            showRatingInResults=showRatingInResults,
        )
        paginator = pages.Paginator(
            pages=page_list, timeout=TIMEOUT_VIEW_RATINGS_PAGINATOR
        )
        await paginator.respond(ctx.interaction)

    # -----------------------------------------------------------------------
    # Commands
    # -----------------------------------------------------------------------

    @albumRatings.command(
        description="Use this command to create a new album rating.",
        guild_ids=[799341195109203998],
    )
    async def create(
        self,
        ctx: discord.ApplicationContext,
        album_name: discord.Option(
            str,
            description="Provide the name of the album. The album must exist on Spotify.",
            required=True,
        ),  # type: ignore
        song_fetch_limit: discord.Option(
            int,
            description="Only return N songs from the album. Useful for Super Deluxe albums with extra fluff.",
            default=50,
            min_value=1,
            max_value=50,
        ),  # type: ignore
    ):
        await ctx.defer()

        attempt = 0
        maxRetries = 2

        while attempt < maxRetries:
            try:
                albumQueryResults = music.searchForAlbumName(
                    album_name, limit=ALBUM_APISEARCH_RESULTS_LIMIT
                )

                if not albumQueryResults["albums"]["items"]:
                    raise Exception("No albums were found with that name!")

                reply = EmbedReply(
                    "Album Ratings - Choose Album",
                    "albumratings",
                    description="Choose the album you wish to rate from the Spotify results below.",
                )

                reply.set_footer(
                    text="Album data provided by Spotify®.",
                    icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png",
                )

                choiceObjects = []

                for idx, album in enumerate(albumQueryResults["albums"]["items"]):
                    choiceObject = {
                        "index": idx,
                        "name": album["name"],
                        "artists": ", ".join(
                            [artist["name"] for artist in album["artists"]]
                        ),
                        "releaseDate": dates.formatSimpleDate(
                            album["release_date"], includeTime=False
                        ),
                        "trackAmount": album["total_tracks"],
                        "spotifyID": album["id"],
                    }

                    choiceObjects.append(choiceObject)

                    reply.add_field(
                        name=f"{choiceObject['index'] + 1}. {choiceObject['name']} · {choiceObject['releaseDate']} ({choiceObject['trackAmount']} Track{'s' if choiceObject['trackAmount'] > 1 else ''})",
                        value=choiceObject["artists"],
                        inline=False,
                    )

                view = music.ChooseAlbumView(choiceObjects)

                msg: discord.WebhookMessage = await ctx.respond(
                    embed=reply, view=view, ephemeral=True
                )
                view.message = msg

                await view.wait()

                try:
                    await msg.delete()
                except discord.NotFound:
                    pass

                albumChoiceID = view.choice

                matchingDuplicateRatings = LocalDatabase(database="albumratings").get(
                    "SELECT * FROM ratings WHERE spotifyAlbumID = ? AND createdBy = ?",
                    (albumChoiceID, ctx.user.id),
                )

                matchingDuplicateRatings = [
                    music.SmallRating(rating) for rating in matchingDuplicateRatings
                ]

                if matchingDuplicateRatings:
                    confirmView = music.DuplicateRatingConfirmationView(
                        originalUser=ctx.user
                    )

                    paginatedResults = await paginateRatingList(
                        matchingDuplicateRatings,
                        bot=self.bot,
                        title="Album Rating - Duplicates Found",
                        description="You have already rated this album before! Are you sure you want to continue?",
                    )

                    paginator: pages.Paginator = pages.Paginator(
                        pages=paginatedResults,
                        custom_view=confirmView,
                        timeout=confirmView.timeout,
                        author_check=False,
                    )

                    confirmView.paginator = paginator

                    duplicateMessage = await paginator.respond(ctx.interaction)

                    timedOut = await paginator.wait()

                    paginator.stop()

                    if timedOut:
                        timedOutReply = EmbedReply(
                            "Album Rating - Duplicates Found - Timed Out",
                            "albumratings",
                            error=True,
                            description=f"You took too long to confirm whether you wanted to continue with duplicate ratings! Try again.\n\nThis message will delete in {DUPLICATE_RATING_TIMEOUT_DELETEAFTER} seconds.",
                        )

                        try:
                            paginator.disable_on_timeout = False

                            await duplicateMessage.edit(
                                embed=timedOutReply,
                                view=None,
                                delete_after=DUPLICATE_RATING_TIMEOUT_DELETEAFTER,
                            )

                            return
                        except discord.NotFound:
                            return

                    if not paginator.custom_view.userAcknowledged:
                        try:
                            await duplicateMessage.delete()

                            return
                        except discord.NotFound:
                            return

                    try:
                        await duplicateMessage.delete()
                    except discord.NotFound:
                        pass

                if albumChoiceID is None:
                    return

                albumDetailsFromID = music.fetchAlbumDetailsByID(albumChoiceID)

                parsedAlbumDetails: music.Album = await music.parseAlbumDetails(
                    albumDetailsFromID, ctx.user, song_fetch_limit
                )

                firstTrack = parsedAlbumDetails.tracks[0]

                view = music.SongRatingView(parsedAlbumDetails)

                wholeAlbumEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)
                songRatingEmbed = music.TrackRatingEmbedReply(firstTrack)

                originalResponse: discord.Message = await ctx.channel.send(
                    embeds=[wholeAlbumEmbed, songRatingEmbed], view=view
                )
                view.message = originalResponse

                timedOut = await view.wait()

                if timedOut or view.cancelled:
                    view.disable_all_items()
                    return

                finishedRatingEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)

                ratingChannel = self.bot.get_channel(RATING_CHANNEL) or ctx.channel

                displayedAlbumReviewMessage: discord.Message = await ratingChannel.send(
                    embed=finishedRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        parsedAlbumDetails.link,
                    ),
                )

                music.commitTrackFlags(parsedAlbumDetails)

                packedAlbumRating = parsedAlbumDetails.packAlbumRating(
                    displayedAlbumReviewMessage
                )

                database = LocalDatabase(database="albumratings")

                database.setOne(
                    """
                    INSERT INTO `ratings` 
                    (`ratingID`, `createdBy`, `createdAt`, `editedAt`, `ratingArtist`, `ratingAlbum`, `spotifyAlbumID`, `formattedRating`, `trackAmount`, `lastRelatedMessage`, `serializedRating`) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        packedAlbumRating.ratingID,
                        packedAlbumRating.createdBy,
                        packedAlbumRating.createdAt,
                        packedAlbumRating.editedAt,
                        packedAlbumRating.ratingArtist,
                        packedAlbumRating.ratingAlbum,
                        packedAlbumRating.spotifyAlbumID,
                        packedAlbumRating.formattedRating,
                        packedAlbumRating.trackAmount,
                        packedAlbumRating.lastRelatedMessage,
                        packedAlbumRating.serializedRating,
                    ),
                )

                await originalResponse.delete()

                savedReply = EmbedReply(
                    "Album Ratings - Create Rating",
                    "albumratings",
                    description=f"Album rating saved. ✅\n\nView rating: {displayedAlbumReviewMessage.jump_url}\n\n(This message will delete after {DELETE_SAVED_REPLY_AFTER} seconds.)",
                )

                await ctx.send(
                    content=ctx.author.mention,
                    embed=savedReply,
                    delete_after=DELETE_SAVED_REPLY_AFTER,
                )

                break
            except requests.exceptions.ConnectionError:
                attempt += 1

                print(f"Spotify Connection attempt {attempt} Failed")

                await asyncio.sleep(SLEEP_BETWEEN_API_ATTEMPTS)

                continue
            except Exception as e:
                reply = _error_reply("Album Ratings - Create Rating - Error", e)
                await reply.send(ctx, ephemeral=False)
                break
        else:
            await msg.delete()

            reply = EmbedReply(
                "Album Ratings - Create Rating - Error",
                "albumratings",
                True,
                description="The Spotify API seems to be having issues right now.\n\nPlease try again later.",
            )

            await reply.send(ctx, ephemeral=False)

    @albumRatings.command(
        description="View an album rating (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    async def view(
        self,
        ctx: discord.ApplicationContext,
        id: discord.Option(
            str,
            description="Provide the Rating ID to view. Use the list command to find this ID.",
            required=True,
        ),  # type: ignore
        send_to_rating_channel: discord.Option(
            bool,
            description="Instead of replying to the command here, send the embed to the rating channel without context.",
            default=True,
        ),  # type: ignore
        edit_original_rating_message: discord.Option(
            bool,
            description="Instead of re-sending the updated rating message, update the original one.",
            default=False,
        ),  # type: ignore
        ephemeral: discord.Option(
            bool,
            description="By default, the rating will only be viewable by you. Set to False to send as a chat reply.",
            default=False,
        ),  # type: ignore
    ):
        try:
            database = LocalDatabase(database="albumratings")

            row = database.get("SELECT * FROM ratings WHERE ratingID = ?", (id,))

            if not row:
                raise Exception(
                    "There were no ratings with that ID found!\n\nTry using the list command to narrow down your search."
                )

            rating = music.SmallRating(row[0])
            unpackedRating = music.unpackAlbumRating(self.bot, rating.serializedRating)
            albumRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            if send_to_rating_channel:
                channel = self.bot.get_channel(RATING_CHANNEL)

                if not channel:
                    raise Exception(
                        "The rating channel could not be found.\n\nSet send_to_rating_channel=False when using this command."
                    )

                ratingMessageReference, _ = await self._publish_rating_message(
                    channel,
                    albumRatingEmbed,
                    unpackedRating.link,
                    rating.lastRelatedMessage,
                    edit_in_place=edit_original_rating_message,
                )

                if not edit_original_rating_message:
                    database.setOne(
                        "UPDATE ratings SET lastRelatedMessage = ? WHERE ratingID = ?",
                        (ratingMessageReference.id, id),
                    )

                reply = EmbedReply(
                    "Album Ratings - View ID",
                    "albumratings",
                    description=f"Successfully retrieved rating for {unpackedRating.name}. ✅\n\nView here: {ratingMessageReference.jump_url}",
                )

                await reply.send(ctx, ephemeral=False)
            else:
                await albumRatingEmbed.send(ctx, ephemeral=ephemeral)
        except Exception as e:
            await _error_reply("Album Ratings - Error", e).send(ctx, ephemeral=False)

    @albumRatings.command(
        description="Edit an album rating (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    async def edit(
        self,
        ctx: discord.ApplicationContext,
        id: discord.Option(
            str,
            description="Provide the Rating ID to edit. Use the list command to find this ID.",
            required=True,
        ),  # type: ignore
        send_to_rating_channel: discord.Option(
            bool,
            description="Instead of replying to the command here, send the embed to the rating channel without context.",
            default=True,
        ),  # type: ignore
        edit_original_rating_message: discord.Option(
            bool,
            description="Instead of re-sending the updated rating message, update the original one.",
            default=True,
        ),  # type: ignore
    ):
        try:
            responseReply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                description=f"The rating editor has been opened for rating {id}.",
            )

            responseMessage = await responseReply.send(ctx, ephemeral=True)
            await responseMessage.delete_original_response()

            await self._albumrating_edit_core(
                user=ctx.user,
                ratingID=id,
                channel=ctx.channel,
                guild=ctx.guild,
                bot=self.bot,
                send_to_rating_channel=send_to_rating_channel,
                edit_original_rating_message=edit_original_rating_message,
            )
        except Exception as e:
            await _error_reply("Album Ratings - Error", e).send(ctx, ephemeral=False)

    async def _albumrating_edit_core(
        self,
        user: discord.User,
        ratingID: str,
        channel: discord.TextChannel,
        guild: discord.Guild,
        bot: discord.Bot,
        original_message: discord.Message | None = None,
        original_interaction: discord.Interaction | None = None,
        send_to_rating_channel: bool = True,
        edit_original_rating_message: bool = True,
    ):
        """Internal version of /albumrating edit that works for both slash and button callbacks.

        When original_message and original_interaction are provided (i.e. triggered from the
        Edit Rating button), the editing UI is shown by editing the original rating message
        in-place rather than sending a new message. The original message is restored once
        editing is complete or cancelled.
        """
        database = LocalDatabase(database="albumratings")

        targetRating = database.get(
            "SELECT * FROM ratings WHERE ratingID = ?", (ratingID,)
        )
        if not targetRating:
            raise Exception("Rating not found in database.")

        rating = music.SmallRating(targetRating[0])
        createdByID = rating.createdBy

        if (createdByID != user.id) and not (await bot.is_owner(user)):
            raise Exception("You do not have permission to edit this rating.")

        unpackedRating = music.unpackAlbumRating(bot, rating.serializedRating)
        firstTrack = unpackedRating.tracks[0]

        albumEmbed = music.AlbumRatingEmbedReply(unpackedRating)
        trackEmbed = music.TrackRatingEmbedReply(firstTrack)

        in_place = original_message is not None and original_interaction is not None

        async def _restore_original_message():
            try:
                currentRating = database.get(
                    "SELECT * FROM ratings WHERE ratingID = ?", (ratingID,)
                )
                if currentRating:
                    restored = music.unpackAlbumRating(
                        bot, music.SmallRating(currentRating[0]).serializedRating
                    )
                    restoredEmbed = music.AlbumRatingEmbedReply(restored)
                    await original_message.edit(
                        embeds=[restoredEmbed],
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            restored.link
                        ),
                    )
            except Exception:
                pass

        view = music.SongRatingView(
            unpackedRating,
            restore_callback=_restore_original_message if in_place else None,
        )

        if in_place:
            await original_interaction.response.edit_message(
                embeds=[albumEmbed, trackEmbed],
                view=view,
            )
            editMsg = original_message
        else:
            editMsg: discord.Message = await channel.send(
                embeds=[albumEmbed, trackEmbed],
                view=view,
            )

        view.message = editMsg

        async def _cleanup_edit_msg():
            if in_place:
                await _restore_original_message()
            else:
                try:
                    await editMsg.delete()
                except discord.errors.NotFound:
                    pass

        try:
            timedOut = await view.wait()
        except Exception as e:
            await _cleanup_edit_msg()
            raise e

        if timedOut or view.cancelled:
            await _cleanup_edit_msg()
            return

        unpackedRating.updateEditedTime()
        finishedEmbed = music.AlbumRatingEmbedReply(unpackedRating)

        ratingChannel = bot.get_channel(RATING_CHANNEL)
        if not ratingChannel:
            await _cleanup_edit_msg()
            raise Exception("The rating channel could not be found.")

        if in_place:
            ratingMessage = await editMsg.edit(
                embeds=[finishedEmbed],
                view=music.FinishedRatingPersistentMessageButtonsView(
                    unpackedRating.link
                ),
            )
        else:
            ratingMessage, _ = await self._publish_rating_message(
                ratingChannel,
                finishedEmbed,
                unpackedRating.link,
                rating.lastRelatedMessage,
                edit_in_place=edit_original_rating_message,
            )

            try:
                await editMsg.delete()
            except discord.errors.NotFound:
                pass

        music.commitTrackFlags(unpackedRating)   # <-- add here

        packedAlbumRating = unpackedRating.packAlbumRating(ratingMessage)
        database.setOne(
            """
            UPDATE ratings
            SET editedAt = ?, formattedRating = ?, lastRelatedMessage = ?, serializedRating = ?
            WHERE ratingID = ?
            """,
            (
                packedAlbumRating.editedAt,
                packedAlbumRating.formattedRating,
                packedAlbumRating.lastRelatedMessage,
                packedAlbumRating.serializedRating,
                ratingID,
            ),
        )

        savedReply = EmbedReply(
            "Album Ratings - Edited",
            "albumratings",
            description=(
                f"Album rating edited successfully. ✅\n\n"
                f"View rating: {ratingMessage.jump_url}\n\n"
                f"(This message will delete after {DELETE_SAVED_REPLY_AFTER} seconds.)"
            ),
        )

        await channel.send(
            content=user.mention,
            embed=savedReply,
            delete_after=DELETE_SAVED_REPLY_AFTER,
        )

    @albumRatings.command(
        description="Change the date an album was rated on (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    async def changedate(
        self,
        ctx: discord.ApplicationContext,
        id: discord.Option(
            str,
            description="Provide the Rating ID to edit. Use the list command to find this ID.",
            required=True,
        ),  # type: ignore
        newdate: discord.Option(
            str,
            description="The date string of the new target rating date. Example: 01/31/2025 12:34:56",
            required=True,
        ),  # type: ignore
        send_to_rating_channel: discord.Option(
            bool,
            description="Instead of replying to the command here, send the embed to the rating channel without context.",
            default=True,
        ),  # type: ignore
        edit_original_rating_message: discord.Option(
            bool,
            description="Instead of re-sending the updated rating message, update the original one.",
            default=True,
        ),  # type: ignore
    ):
        try:
            newDate = dates.simpleDateObj(newdate)

            ratingChannel = self.bot.get_channel(RATING_CHANNEL)

            if not ratingChannel and (
                edit_original_rating_message or send_to_rating_channel
            ):
                raise Exception(
                    "The rating channel could not be found.\n\nSet send_to_rating_channel=False and edit_original_rating_message=False when using this command."
                )

            database, rating = await self._fetch_and_authorize_rating(id, ctx.user)

            unpackedRating = music.unpackAlbumRating(self.bot, rating.serializedRating)

            oldDate = unpackedRating.createdAt
            unpackedRating.createdAt = newDate

            finishedRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            if send_to_rating_channel:
                ratingMessageReference, warning = await self._publish_rating_message(
                    ratingChannel,
                    finishedRatingEmbed,
                    unpackedRating.link,
                    rating.lastRelatedMessage,
                    edit_in_place=edit_original_rating_message,
                )
            else:
                finishedSentRating = await finishedRatingEmbed.send(ctx, ephemeral=True)

                try:
                    ratingMessageReference = await ratingChannel.fetch_message(
                        rating.lastRelatedMessage
                    )
                except discord.errors.NotFound:
                    ratingMessageReference = (
                        await finishedSentRating.original_response()
                    )

                warning = ""

            packedAlbumRating = unpackedRating.packAlbumRating(ratingMessageReference)

            database.setOne(
                """
                UPDATE `ratings` 
                SET createdAt = ?, lastRelatedMessage = ?, serializedRating = ?
                WHERE ratingID = ?
                """,
                (
                    packedAlbumRating.createdAt,
                    packedAlbumRating.lastRelatedMessage,
                    packedAlbumRating.serializedRating,
                    id,
                ),
            )

            savedReply = EmbedReply(
                "Album Ratings - Change Date",
                "albumratings",
                description=(
                    f"Album rating date changed. ✅\n\n"
                    f"Old Date: {dates.formatSimpleDate(oldDate, discordDateFormat='f')}\n"
                    f"New Date: {dates.formatSimpleDate(newDate, discordDateFormat='f')}\n\n"
                    f"View rating: {ratingMessageReference.jump_url}{warning}"
                ),
            )

            await savedReply.send(ctx, ephemeral=False)
        except Exception as e:
            await _error_reply("Album Ratings - Error", e).send(ctx, ephemeral=False)

    @albumRatings.command(
        description="Delete an album rating (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    async def delete(
        self,
        ctx: discord.ApplicationContext,
        id: discord.Option(
            str,
            description="Provide the Rating ID to view. Use the list command to find this ID.",
            required=True,
        ),  # type: ignore
        delete_rating_message: discord.Option(
            bool,
            description="Also delete the embed sent to the rating channel.",
            default=True,
        ),  # type: ignore
    ):
        try:
            database, rating = await self._fetch_and_authorize_rating(id, ctx.user)

            unpackedRating = music.unpackAlbumRating(self.bot, rating.serializedRating)

            formattedCreatedAt = dates.formatSimpleDate(
                unpackedRating.createdAt, discordDateFormat="d"
            )
            prettyAlbumName = text.truncateString(
                f"{unpackedRating.name} · {unpackedRating.getArtists(True)} · {formattedCreatedAt}",
                256,
            )[0]

            confirmationReplyEmbed = EmbedReply(
                "Album Ratings - Delete Rating",
                "albumratings",
                description="Are you sure you want to delete the following rating?",
            )

            confirmationReplyEmbed.add_field(
                name=prettyAlbumName, value=f"Rating ID: {unpackedRating.ratingID}"
            )

            confirmationReplyView = music.DeleteRatingView()

            confirmationReply = await ctx.respond(
                embed=confirmationReplyEmbed, view=confirmationReplyView, ephemeral=True
            )

            timedOut = await confirmationReplyView.wait()

            if timedOut:
                reply = EmbedReply(
                    "Album Ratings - Delete Rating",
                    "albumratings",
                    True,
                    description="You ran out of time to delete the rating. Please try again.",
                )

                await confirmationReply.edit_original_response(embed=reply, view=None)
                return

            if not confirmationReplyView.confirmDelete:
                await confirmationReply.delete_original_response()
                return

            if delete_rating_message:
                channel = self.bot.get_channel(RATING_CHANNEL)

                if not channel:
                    raise Exception(
                        "The rating channel could not be found.\n\nSet delete_rating_message=False when using this command."
                    )

                try:
                    oldMessageReference = await channel.fetch_message(
                        rating.lastRelatedMessage
                    )
                    await oldMessageReference.delete()
                except discord.errors.NotFound:
                    pass

            database.setOne("DELETE FROM trackFlags WHERE rating = ?", (id,))
            database.setOne("DELETE FROM ratings WHERE ratingID = ?", (id,))

            reply = EmbedReply(
                "Album Ratings - Deleted",
                "albumratings",
                description="Successfully deleted rating. ✅",
            )

            reply.add_field(
                name=prettyAlbumName, value=f"Rating ID: {unpackedRating.ratingID}"
            )

            await confirmationReply.edit_original_response(embed=reply, view=None)
        except Exception as e:
            await _error_reply("Album Ratings - Error", e).send(ctx, ephemeral=False)

    @albumRatings.command(
        description="OWNER ONLY: Reassign an album rating to a new user (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    @is_owner_only()
    async def changerater(
        self,
        ctx: discord.ApplicationContext,
        id: str,
        new: discord.Option(discord.Member),  # type: ignore
    ):
        msg = await ctx.send_response("done")

        database = LocalDatabase(database="albumratings")

        initialSearch = database.get(
            "SELECT * FROM ratings WHERE ratingID = ?",
            (id,),
        )

        rating = music.SmallRating(initialSearch[0])

        unpack = music.unpackAlbumRating(self.bot, rating.serializedRating)

        unpack.setCreatedBy(new)

        pack = unpack.packAlbumRating(msg)

        database.setOne(
            """
            UPDATE `ratings` 
            SET createdBy = ?, serializedRating = ?
            WHERE ratingID = ?
            """,
            (
                pack.createdBy,
                pack.serializedRating,
                id,
            ),
        )

    list_ratings = albumRatings.create_subgroup(
        "list",
        "Use these commands to list ratings based on metrics.",
        guild_ids=[799341195109203998],
    )

    @list_ratings.command(
        description="Average rating for all people that have rated the album (by Album Name).",
        guild_ids=[799341195109203998],
    )
    async def average(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(
            str, description="The album to search for ratings for (by Album Name)."
        ),  # type: ignore
        ephemeral: discord.Option(
            bool,
            description="By default, the average rating will be public. Set to True to only be viewable by you.",
            default=False,
        ),  # type: ignore
    ):
        try:
            await ctx.defer()

            database = LocalDatabase(database="albumratings")

            initialSearch = database.get(
                "SELECT * FROM ratings WHERE ratingAlbum LIKE ? ORDER BY createdAt DESC",
                ("%" + query + "%",),
                limit=1,
            )

            if not initialSearch:
                raise Exception(
                    f"No ratings found for query '{query}'.\n\nTry again with less keywords for a broader search."
                )

            initialSearchResult = music.SmallRating(initialSearch[0])

            allRatingsForAlbumResult = database.get(
                "SELECT * FROM ratings WHERE spotifyAlbumID = ? ORDER BY createdAt DESC",
                (initialSearchResult.spotifyAlbumID,),
            )

            allRatingsForAlbumResult = [
                music.SmallRating(rating) for rating in allRatingsForAlbumResult
            ]

            unpackedRatings = [
                music.unpackAlbumRating(self.bot, ratingResult.serializedRating)
                for ratingResult in allRatingsForAlbumResult
            ]

            reply = music.AlbumRatingEmbedReply(unpackedRatings)

            await reply.send(ctx, ephemeral=ephemeral)
        except Exception as e:
            await _error_reply("Album Ratings - Album Rating Average", e).send(
                ctx, ephemeral=False
            )

    @list_ratings.command(
        description="List album ratings (by Search Term [artist or album_name]).",
        guild_ids=[799341195109203998],
    )
    async def search(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(
            str, description="The name of the album or artist to search ratings for."
        ),  # type: ignore
        member: discord.Option(
            discord.Member,
            description="Optional: Filter the results to ratings by a specific member.",
            required=False,
        ) = None,  # type: ignore
    ):
        try:
            database = LocalDatabase(database="albumratings")

            sql = "SELECT * FROM ratings WHERE (ratingAlbum LIKE ? OR ratingArtist LIKE ?) "
            params = ("%" + query + "%", "%" + query + "%")

            if member:
                sql += "AND createdBy = ? "
                params += (member.id,)

            sql += "ORDER BY createdAt DESC"

            results = [music.SmallRating(r) for r in database.get(sql, params)]

            if not results:
                member_filter_text = f" by {member.display_name}" if member else ""
                raise Exception(
                    f"No ratings found for query '{query}'{member_filter_text}.\n\nTry again with less keywords for a broader search."
                )

            member_desc = f" by {member.mention}" if member else ""

            await self._respond_with_rating_list(
                ctx,
                results,
                "Album Ratings - List By Search",
                f"List of ratings for query '{query}'{member_desc}. ({len(results)} Total)",
                showUserInResults=True,
            )
        except discord.NotFound:
            pass
        except Exception as e:
            await _error_reply("Album Ratings - List By Search", e).send(
                ctx, ephemeral=False
            )

    @list_ratings.command(
        description="List album ratings (by Member).", guild_ids=[799341195109203998]
    )
    async def member(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Option(
            discord.Member,
            description="Provide the guild member to inquiry ratings for.",
            required=False,
        ),  # type: ignore
        album_query: discord.Option(
            str,
            description="Optional: Filter the member's ratings by album or artist keyword.",
            required=False,
        ) = None,  # type: ignore
    ):
        await ctx.defer()

        member: discord.Member = member if member else ctx.user

        try:
            database = LocalDatabase(database="albumratings")

            sql = "SELECT * FROM ratings WHERE createdBy = ? "
            params = (member.id,)

            if album_query:
                sql += "AND (ratingAlbum LIKE ? OR ratingArtist LIKE ?) "
                params += ("%" + album_query + "%", "%" + album_query + "%")

            sql += "ORDER BY createdAt DESC"

            results = [music.SmallRating(r) for r in database.get(sql, params)]

            if not results:
                album_filter_text = (
                    f" containing '{album_query}'" if album_query else ""
                )
                raise Exception(
                    f"The user {member.mention} does not have any ratings{album_filter_text} yet!\n\nGet started with /albumratings create."
                )

            album_desc = f" filtered by '{album_query}'" if album_query else ""

            await self._respond_with_rating_list(
                ctx,
                results,
                "Album Ratings - List By Member",
                f"List of ratings for {member.mention}{album_desc} ({len(results)} Total)",
            )
        except discord.NotFound:
            pass
        except Exception as e:
            await _error_reply("Album Ratings - List By Member", e).send(
                ctx, ephemeral=False
            )

    @list_ratings.command(
        description="List the top album ratings for a member",
        guild_ids=[799341195109203998],
    )
    async def top(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Option(
            discord.Member,
            description="Provide the guild member to inquiry ratings for.",
            required=False,
        ),  # type: ignore
        include_singles: discord.Option(
            bool,
            description="Filter results such that there are no single track albums clogging up the list.",
            default=False,
        ),  # type: ignore
        ascending: discord.Option(
            bool,
            description="Filter in reverse order? (Worst album first.)",
            default=False,
        ),  # type: ignore
    ):
        await ctx.defer()

        member: discord.Member = member if member else ctx.user

        try:
            database = LocalDatabase(database="albumratings")

            sql = f'SELECT * FROM ratings WHERE createdBy = ? AND formattedRating != "Unfinished"'

            if not include_singles:
                sql += f" AND trackAmount > {SINGLE_ALBUM_TRACK_CRITERIA}"

            results = database.get(sql, (member.id,))

            if not results:
                raise Exception(
                    f"The user {member.mention} does not have any ratings that match the criteria yet!\n\nGet started with `/albumratings create`"
                )

            results = [music.SmallRating(r) for r in results]
            results.sort(key=music.sortByRating, reverse=not ascending)

            await self._respond_with_rating_list(
                ctx,
                results,
                "Album Ratings - List Top",
                f"List of top ratings for {member.mention}, sorted in {'ascending' if ascending else 'descending'} order. {'(No Singles)' if not include_singles else '(With Singles)'} ({len(results)} Total)",
            )
        except discord.NotFound:
            pass
        except Exception as e:
            await _error_reply("Album Ratings - List Top", e).send(ctx, ephemeral=False)

    @list_ratings.command(
        description="List the hall of fame songs for a member",
        guild_ids=[799341195109203998],
    )
    async def hof(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Option(
            discord.Member,
            description="Provide the guild member to inquiry ratings for.",
            required=False,
        ),  # type: ignore
    ):
        await ctx.defer()

        member: discord.Member = member if member else ctx.user

        try:
            database = LocalDatabase(database="albumratings")

            # Fixed `createdBy` to `raterID` to match the insertion query from music.py
            results = database.get(
                "SELECT * FROM trackFlags WHERE flagID = ? AND raterID = ?",
                ("hof", member.id),
            )

            if not results:
                raise Exception(
                    f"The user {member.mention} does not have any songs in the hall of fame yet!\n\nGet started with `/albumratings create` and use the 👑 flag to add songs to the hall of fame."
                )

            # Sort by dateAdded (index 6) in descending order
            results.sort(key=lambda row: row[6], reverse=True)

            pages_list = []
            guild_id = ctx.guild_id

            # Paginate all of the hall of fame songs into embeds of LIST_RATINGS_PER_PAGE songs each
            for chunk in range(0, len(results), LIST_RATINGS_PER_PAGE):
                page = EmbedReply(
                    "Album Ratings - Hall of Fame",
                    "albumratings",
                    description=f"Hall of Fame songs for {member.mention} ({len(results)} Total)",
                )

                for row in results[chunk : chunk + LIST_RATINGS_PER_PAGE]:
                    # Map SQL row indices based on the insert in music.py
                    trackName = row[2]
                    albumName = row[4]
                    dateAdded = row[6]
                    artistName = row[7]
                    ratingID = row[9]

                    # Parse date string to Discord formatted timestamp
                    try:
                        dt = dates.simpleDateObj(dateAdded)
                        formattedDate = dates.formatSimpleDate(
                            dt, discordDateFormat="d"
                        )
                    except Exception:
                        formattedDate = dateAdded

                    title = text.truncateString(f"👑 {trackName} · {artistName}", 256)[
                        0
                    ]
                    descriptor = f"Album: {albumName}\nAdded: {formattedDate}"

                    # Backlink to the rating message via the ratingID
                    ratingRow = database.get(
                        "SELECT lastRelatedMessage FROM ratings WHERE ratingID = ?",
                        (ratingID,),
                    )
                    if ratingRow and ratingRow[0][0] and guild_id:
                        oldMessageID = ratingRow[0][0]
                        jump_url = f"https://discord.com/channels/{guild_id}/{RATING_CHANNEL}/{oldMessageID}"
                        descriptor += f"\nView Rating: {jump_url}"
                    else:
                        descriptor += f"\nRating ID: {ratingID}"

                    page.add_field(name=title, value=descriptor, inline=False)

                pages_list.append(page)

            # Use the pages Paginator from Pycord to finalize the view
            paginator = pages.Paginator(
                pages=pages_list, timeout=TIMEOUT_VIEW_RATINGS_PAGINATOR
            )
            await paginator.respond(ctx.interaction)

        except discord.NotFound:
            pass
        except Exception as e:
            await _error_reply("Album Ratings - List Hall of Fame", e).send(
                ctx, ephemeral=False
            )

    @albumRatings.command(
        description="Update the persistent buttons on all ratings. (OWNER ONLY)",
        guild_ids=[799341195109203998],
    )
    @is_owner_only()
    async def updateviews(
        self,
        ctx: discord.ApplicationContext,
        sleep_delay: discord.Option(
            float,
            description="Time to wait in seconds for rate limit avoidance.",
            default=0.5,
            min_value=0.1,
            max_value=60,
        ),  # type: ignore
    ):
        await ctx.defer()

        database = LocalDatabase(database="albumratings")

        res = database.get("SELECT * FROM ratings")

        for i in res:
            try:
                rating = music.SmallRating(i)
                ratingChannel = await self.bot.fetch_channel(RATING_CHANNEL)

                targetMessage = await ratingChannel.fetch_message(
                    rating.lastRelatedMessage
                )

                await targetMessage.edit(
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        f"https://open.spotify.com/album/{rating.spotifyAlbumID}",
                    )
                )

                await asyncio.sleep(sleep_delay)
            except discord.NotFound:
                pass

        reply = EmbedReply(
            "Album Ratings - Update Views",
            "albumratings",
            description="All ratings updated!",
        )

        await reply.send(ctx)

    @albumRatings.command(
        description="Update the objects in the DB on all ratings. (OWNER ONLY)",
        guild_ids=[799341195109203998],
    )
    @is_owner_only()
    async def updateallobjects(
        self,
        ctx: discord.ApplicationContext,
    ):
        await ctx.defer()

        database = LocalDatabase(database="albumratings")
        results = database.get("SELECT * FROM ratings")

        rating_channel = self.bot.get_channel(RATING_CHANNEL) or await self.bot.fetch_channel(RATING_CHANNEL)

        old_domains = (
            "i.breia.net",
            "cdn.breia.net",
            "cdn.brendenian.net",
            "i.brendenian.net",
        )

        def update_image_url(url: str | None) -> str | None:
            if not url or not any(domain in url for domain in old_domains):
                return url

            parsed = urllib.parse.urlparse(url)
            filename = posixpath.basename(parsed.path).lower()
            return f"https://files.brendenian.net/BRNDN/{filename}"

        for result in results:
            try:
                rating = music.SmallRating(result)
                unpackedRating = music.unpackAlbumRating(self.bot, rating.serializedRating)

                updated = False

                # Check and update coverImage
                if unpackedRating.coverImage and any(domain in unpackedRating.coverImage for domain in old_domains):
                    unpackedRating.coverImage = update_image_url(unpackedRating.coverImage)
                    updated = True

                # Check and update customCoverImage if present
                if getattr(unpackedRating, "customCoverImage", None) and any(
                    domain in unpackedRating.customCoverImage for domain in old_domains
                ):
                    unpackedRating.customCoverImage = update_image_url(unpackedRating.customCoverImage)
                    updated = True

                # Fetch the associated message
                target_message: discord.Message | None = None
                if rating.lastRelatedMessage and rating_channel:
                    try:
                        target_message = await rating_channel.fetch_message(rating.lastRelatedMessage)
                    except (discord.NotFound, discord.HTTPException):
                        target_message = None

                # Edit the message BEFORE packing, because packAlbumRating destructively 
                # changes unpackedRating.createdBy into an integer
                if target_message:
                    finishedEmbed = music.AlbumRatingEmbedReply(unpackedRating)
                    view = music.FinishedRatingPersistentMessageButtonsView(unpackedRating.link)
                    await target_message.edit(embed=finishedEmbed, view=view)
                    await asyncio.sleep(0.5)

                # Pack the updated album rating
                message_ref = target_message or discord.Object(id=rating.lastRelatedMessage)
                packedAlbumRating = unpackedRating.packAlbumRating(message_ref)

                # Update the serialized rating in the database
                database.setOne(
                    """
                    UPDATE ratings
                    SET serializedRating = ?
                    WHERE ratingID = ?
                    """,
                    (
                        packedAlbumRating.serializedRating,
                        rating.ratingID,
                    ),
                )

            except Exception as e:
                print(f"Failed to update rating row {result[0]}: {e}")
                continue

        reply = EmbedReply(
            "Album Ratings - Update All Objects",
            "albumratings",
            description="All ratings updated!",
        )

        await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
