import discord
import requests
import asyncio
import sys
from discord.ext import commands, pages

from src.classes import *
from src.utils import music
from src.utils import dates

RATING_CHANNEL = 946507420916678688

LIST_RATINGS_PER_PAGE = 10

DELETE_SAVED_REPLY_AFTER = 15

ALBUM_APISEARCH_RESULTS_LIMIT = 5

SLEEP_BETWEEN_API_ATTEMPTS = 2

async def paginateRatingList(
    results: list[tuple],
    bot: discord.Bot,
    title: str,
    description: str,
    *,
    showUserInResults: bool = False,
) -> list[pages.Page]:
    pageList = []

    for chunk in range(0, len(results), LIST_RATINGS_PER_PAGE):
        page = EmbedReply(title, "albumratings", description=description)

        for result in results[chunk : chunk + LIST_RATINGS_PER_PAGE]:
            formattedCreatedAt = dates.formatSimpleDate(
                result[2], discordDateFormat="d"
            )

            formattedRatingName = text.truncateString(
                f"{result[5]} · {result[4]} · {formattedCreatedAt}", 256
            )[0]

            descriptor = f"Rating ID: {result[0]}"

            if showUserInResults:
                descriptor += f"\nRating By: <@{result[1]}>"

            oldMessageID = result[8]
            ratingChannel = bot.get_channel(RATING_CHANNEL)

            try:
                oldMessageReference = await ratingChannel.fetch_message(
                    oldMessageID
                )

                descriptor += f"\nView: {oldMessageReference.jump_url}"
            except discord.errors.NotFound:
                pass

            page.add_field(name=formattedRatingName, value=descriptor, inline=False)

        pageList.append(page)

    return pageList


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

                msg: discord.WebhookMessage = await ctx.respond(embed=reply, view=view, ephemeral=True)
                view.message = msg

                await view.wait()

                if view.choice == None:
                    return

                albumDetailsFromID = music.fetchAlbumDetailsByID(view.choice)

                parsedAlbumDetails: music.Album = music.parseAlbumDetails(
                    albumDetailsFromID, ctx.user, song_fetch_limit
                )

                firstTrack = parsedAlbumDetails.tracks[0]

                view = music.SongRatingView(parsedAlbumDetails)

                wholeAlbumEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)
                songRatingEmbed = music.TrackRatingEmbedReply(firstTrack)

                await msg.delete()

                originalResponse: discord.Message = await ctx.channel.send(
                    embeds=[wholeAlbumEmbed, songRatingEmbed], view=view
                )
                view.message = originalResponse

                timedOut = await view.wait()

                if timedOut or view.cancelled:
                    view.disable_all_items()

                    return

                finishedRatingEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)

                ratingChannel = self.bot.get_channel(RATING_CHANNEL)

                if not ratingChannel:
                    ratingChannel = ctx.channel

                displayedAlbumReviewMessage: discord.Message = await ratingChannel.send(
                    embed=finishedRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        parsedAlbumDetails.link,
                    )
                )

                packedAlbumRating = parsedAlbumDetails.packAlbumRating(
                    displayedAlbumReviewMessage
                )

                database = LocalDatabase()

                database.setOne(
                    """
                    INSERT INTO `albumRatings` 
                    (`ratingID`, `createdBy`, `createdAt`, `editedAt`, `ratingArtist`, `ratingAlbum`, `spotifyAlbumID`, `formattedRating`, `lastRelatedMessage`, `serializedRating`) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    packedAlbumRating,
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
                reply = EmbedReply(
                    "Album Ratings - Error", "albumratings", True, description=str(e)
                )

                await reply.send(ctx, ephemeral=True)

                break
        else:
            await msg.delete()

            reply = EmbedReply(
                "Album Ratings - Error",
                "albumratings",
                True,
                description="The Spotify API seems to be having issues right now.\n\nPlease try again later.",
            )

            await reply.send(ctx, ephemeral=True)

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
            default=True,
        ),  # type: ignore
    ):
        try:
            database = LocalDatabase()

            targetRating = database.get(
                "SELECT * FROM albumRatings WHERE ratingID = ?", (id,)
            )

            if not targetRating:
                raise Exception(
                    "There were no ratings with that ID found!\n\nTry using the list command to narrow down your search."
                )

            packedRating = targetRating[0]
            oldMessageID = packedRating[8]

            unpackedRating = music.unpackAlbumRating(self.bot, packedRating[-1])

            albumRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            if send_to_rating_channel:
                channel = self.bot.get_channel(RATING_CHANNEL)

                if not channel:
                    raise Exception(
                        "The rating channel could not be found.\n\nSet send_to_rating_channel=False when using this command."
                    )

                oldMessageReference = None

                try:
                    oldMessageReference = await channel.fetch_message(oldMessageID)

                    if not edit_original_rating_message:
                        await oldMessageReference.delete()

                except discord.errors.NotFound:
                    pass

                if not edit_original_rating_message:
                    ratingMessageReference = await channel.send(
                        embed=albumRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )
                elif oldMessageReference and edit_original_rating_message:
                    ratingMessageReference = await oldMessageReference.edit(
                        embed=albumRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )
                else:
                    raise Exception(
                        "Old message could not be found and edit_original_rating_message=True..."
                    )

                if not edit_original_rating_message:
                    database.setOne(
                        "UPDATE albumRatings SET lastRelatedMessage = ? WHERE ratingID = ?",
                        (ratingMessageReference.id, id),
                    )

                reply = EmbedReply(
                    "Album Ratings - View ID",
                    "albumratings",
                    description=f"Successfully retrieved rating for {unpackedRating.name}. ✅\n\nView here: {ratingMessageReference.jump_url}",
                )

                await reply.send(ctx, ephemeral=True)
            else:
                await albumRatingEmbed.send(ctx, ephemeral=ephemeral)
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

    @albumRatings.command(
        description="OWNER ONLY: Reassign an album rating to a new user (by Rating ID).",
        guild_ids=[799341195109203998],
    )
    async def changerater(
        self,
        ctx: discord.ApplicationContext,
        id: str,
        new: discord.Option(discord.Member),  # type: ignore
    ):
        if not await self.bot.is_owner(ctx.user):
            await ctx.send_response("piss off")

            return

        msg = await ctx.send_response("done")

        database = LocalDatabase()

        initialSearch = database.get(
            "SELECT * FROM albumRatings WHERE ratingID = ?",
            (id,),
        )

        unpack = music.unpackAlbumRating(self.bot, initialSearch[0][-1])

        unpack.createdBy = new

        pack = unpack.packAlbumRating(msg)

        database.setOne(
            """
            UPDATE `albumRatings` 
            SET createdBy = ?, serializedRating = ?
            WHERE ratingID = ?
            """,
            (
                pack[1],
                pack[-1],
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

            database = LocalDatabase()

            initialSearch = database.get(
                "SELECT * FROM albumRatings WHERE ratingAlbum LIKE ? ORDER BY createdAt DESC",
                ("%" + query + "%",),
                limit=1,
            )

            if not initialSearch:
                raise Exception(
                    f"No ratings found for query '{query}'.\n\nTry again with less keywords for a broader search."
                )

            initialSearchResult = initialSearch[0]

            allRatingsForAlbumResult = database.get(
                "SELECT * FROM albumRatings WHERE spotifyAlbumID = ? ORDER BY createdAt DESC",
                (initialSearchResult[6],),
            )

            unpackedRatings = [
                music.unpackAlbumRating(self.bot, ratingResult[-1])
                for ratingResult in allRatingsForAlbumResult
            ]

            reply = music.AlbumRatingEmbedReply(unpackedRatings)

            await reply.send(
                ctx,
                ephemeral=ephemeral,
                view=music.FinishedRatingPersistentMessageButtonsView(
                    unpackedRatings[0].link,
                )
            )
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - Album Rating Average",
                "albumratings",
                True,
                description=str(e),
            )

            await reply.send(ctx, ephemeral=True)


    @list_ratings.command(
        description="List album ratings (by Search Term [artist or album_name]).",
        guild_ids=[799341195109203998],
    )
    async def search(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(
            str,
            description="The name of the album or artist to search ratings for."
        ), # type: ignore
    ):
        try:
            database = LocalDatabase()

            results = database.get(
                "SELECT * FROM albumRatings WHERE ratingAlbum LIKE ? OR ratingArtist LIKE ? ORDER BY createdAt DESC",
                ("%" + query + "%", "%" + query + "%"),
            )

            if not results:
                raise Exception(
                    f"No ratings found for query '{query}'.\n\nTry again with less keywords for a broader search."
                )

            pageList = await paginateRatingList(
                results,
                self.bot,
                "Album Ratings - List By Search",
                f"List of ratings for query '{query}'. ({len(results)} Total)",
                showUserInResults=True,
            )

            pagignator = pages.Paginator(
                pages=pageList,
            )

            await pagignator.respond(ctx.interaction)
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - List By Search",
                "albumratings",
                True,
                description=str(e),
            )

            await reply.send(ctx, ephemeral=True)

    @list_ratings.command(
        description="List album ratings (by Member).", guild_ids=[799341195109203998]
    )
    async def member(
        self,
        ctx: discord.ApplicationContext,
        member: discord.Option(
            discord.Member,
            description="Provide the guild member to inquiry ratings for.",
            required=True,
        ),  # type: ignore
    ):
        member: discord.Member = member

        try:
            database = LocalDatabase()

            results = database.get(
                "SELECT * FROM albumRatings WHERE createdBy = ? ORDER BY createdAt DESC",
                (member.id,),
            )

            if not results:
                raise Exception(
                    f"The user {member.mention} does not have any ratings yet!\n\nGet started with /albumratings create."
                )

            pageList = await paginateRatingList(
                results,
                self.bot,
                "Album Ratings - List By Member",
                f"List of ratings for {member.mention}. ({len(results)} Total)",
            )

            pagignator = pages.Paginator(
                pages=pageList,
            )

            await pagignator.respond(ctx.interaction)
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - List By Member",
                "albumratings",
                True,
                description=str(e),
            )

            await reply.send(ctx, ephemeral=True)

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
            ratingChannel = self.bot.get_channel(RATING_CHANNEL)

            if not ratingChannel and (
                send_to_rating_channel or edit_original_rating_message
            ):
                raise Exception(
                    "The rating channel could not be found.\n\nSet send_to_rating_channel=False and edit_original_rating_message=False when using this command."
                )

            database = LocalDatabase()

            targetRating = database.get(
                "SELECT * FROM albumRatings WHERE ratingID = ?", (id,)
            )

            if not targetRating:
                raise Exception(
                    "There were no ratings with that ID found!\n\nTry using the list command to narrow down your search."
                )

            packedRating = targetRating[0]
            oldMessageID = packedRating[8]
            createdByID = packedRating[1]
            invokedBy: discord.User = ctx.user

            if (createdByID != invokedBy.id) and not (
                await self.bot.is_owner(invokedBy)
            ):
                raise Exception(
                    f"That's not your rating!\n\nTo see a list of your ratings, use: `/albumrating list member member:@{invokedBy.name}`"
                )

            unpackedRating = music.unpackAlbumRating(self.bot, packedRating[-1])

            firstTrack = unpackedRating.tracks[0]

            view = music.SongRatingView(unpackedRating)

            wholeAlbumEmbed = music.AlbumRatingEmbedReply(unpackedRating)
            songRatingEmbed = music.TrackRatingEmbedReply(firstTrack)

            responseReply = EmbedReply(
                "Album Ratings - Edit Rating",
                "albumratings",
                description=f"The rating editor has been opened for rating {id}.",
            )

            responseMessage: discord.Interaction = await responseReply.send(
                ctx, ephemeral=True
            )

            await responseMessage.delete_original_response()

            originalMessage: discord.Message = await ctx.send(
                embeds=[wholeAlbumEmbed, songRatingEmbed], view=view
            )
            view.message = originalMessage

            timedOut = await view.wait()

            if timedOut or view.cancelled:
                view.disable_all_items()

                return

            unpackedRating.updateEditedTime()

            finishedRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            if send_to_rating_channel:
                oldMessageNotFoundWarning: str = ""

                oldMessageReference = None

                try:
                    oldMessageReference = await ratingChannel.fetch_message(
                        oldMessageID
                    )
                except discord.errors.NotFound:
                    oldMessageNotFoundWarning = "\n\n⚠️WARN: The original message tied to this rating could not be found and edit_original_rating_message was set to True when this command was invoked. Instead of editing the message, a new one was sent and can be found through the link above."

                    pass

                if not oldMessageNotFoundWarning and edit_original_rating_message:
                    ratingMessageReference = await oldMessageReference.edit(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )
                else:
                    if oldMessageReference:
                        await oldMessageReference.delete()

                    ratingMessageReference = await ratingChannel.send(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )

                packedAlbumRating = unpackedRating.packAlbumRating(
                    ratingMessageReference
                )

                database.setOne(
                    """
                    UPDATE `albumRatings` 
                    SET editedAt = ?, formattedRating = ?, lastRelatedMessage = ?, serializedRating = ?
                    WHERE ratingID = ?
                    """,
                    (
                        packedAlbumRating[3],
                        packedAlbumRating[7],
                        packedAlbumRating[8],
                        packedAlbumRating[9],
                        id,
                    ),
                )

                await originalMessage.delete()

                savedReply = EmbedReply(
                    "Album Ratings - Edited",
                    "albumratings",
                    description=f"Album rating edited. ✅\n\nView rating: {ratingMessageReference.jump_url}{oldMessageNotFoundWarning}\n\n(This message will delete after {DELETE_SAVED_REPLY_AFTER} seconds.)",
                )

                await ctx.send(
                    content=ctx.author.mention,
                    embed=savedReply,
                    delete_after=DELETE_SAVED_REPLY_AFTER,
                )
            else:
                await originalMessage.edit(
                    embed=finishedRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        unpackedRating.link,
                    )
                )

                packedAlbumRating = unpackedRating.packAlbumRating(originalMessage)

                database.setOne(
                    """
                    UPDATE `albumRatings` 
                    SET editedAt = ?, formattedRating = ?, serializedRating = ?
                    WHERE ratingID = ?
                    """,
                    (
                        packedAlbumRating[3],
                        packedAlbumRating[7],
                        packedAlbumRating[9],
                        id,
                    ),
                )
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

    async def _albumrating_edit_core(
        self,
        user: discord.User,
        ratingID: str,
        channel: discord.TextChannel,
        guild: discord.Guild,
        bot: discord.Bot,
    ):
        """Internal version of /albumrating edit that works for both slash and button callbacks."""
        database = LocalDatabase()

        # Fetch the target rating from DB
        targetRating = database.get("SELECT * FROM albumRatings WHERE ratingID = ?", (ratingID,))
        if not targetRating:
            raise Exception("Rating not found in database.")

        packedRating = targetRating[0]
        oldMessageID = packedRating[8]
        createdByID = packedRating[1]

        # Permission check
        if (createdByID != user.id) and not (await bot.is_owner(user)):
            raise Exception("You do not have permission to edit this rating.")

        # Unpack album rating and build initial view
        unpackedRating = music.unpackAlbumRating(bot, packedRating[-1])
        firstTrack = unpackedRating.tracks[0]

        view = music.SongRatingView(unpackedRating)
        albumEmbed = music.AlbumRatingEmbedReply(unpackedRating)
        trackEmbed = music.TrackRatingEmbedReply(firstTrack)

        # Send editing UI message
        editMsg: discord.Message = await channel.send(
            embeds=[albumEmbed, trackEmbed],
            view=view,
        )
        view.message = editMsg

        try:
            timedOut = await view.wait()
        except Exception as e:
            # Always clean up UI safely
            try:
                await editMsg.delete()
            except discord.errors.NotFound:
                pass
            raise e

        # Handle cancelled or timed-out edit
        if timedOut or view.cancelled:
            try:
                await editMsg.delete()
            except discord.errors.NotFound:
                pass
            return

        # Update rating with new time and embed
        unpackedRating.updateEditedTime()
        finishedEmbed = music.AlbumRatingEmbedReply(unpackedRating)

        # Locate rating channel
        ratingChannel = bot.get_channel(RATING_CHANNEL)
        if not ratingChannel:
            try:
                await editMsg.delete()
            except discord.errors.NotFound:
                pass
            raise Exception("The rating channel could not be found.")

        # Try to edit or recreate the rating message
        try:
            oldMsg = await ratingChannel.fetch_message(oldMessageID)
            ratingMessage = await oldMsg.edit(
                embed=finishedEmbed,
                view=music.FinishedRatingPersistentMessageButtonsView(unpackedRating.link)
            )
        except discord.errors.NotFound:
            ratingMessage = await ratingChannel.send(
                embed=finishedEmbed,
                view=music.FinishedRatingPersistentMessageButtonsView(unpackedRating.link),
            )

        # Update the database
        packedAlbumRating = unpackedRating.packAlbumRating(ratingMessage)
        database.setOne(
            """
            UPDATE albumRatings
            SET editedAt = ?, formattedRating = ?, lastRelatedMessage = ?, serializedRating = ?
            WHERE ratingID = ?
            """,
            (
                packedAlbumRating[3],
                packedAlbumRating[7],
                packedAlbumRating[8],
                packedAlbumRating[9],
                ratingID,
            ),
        )

        # Clean up the edit UI safely
        try:
            await editMsg.delete()
        except discord.errors.NotFound:
            pass

        # Confirmation embed
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

            database = LocalDatabase()

            targetRating = database.get(
                "SELECT * FROM albumRatings WHERE ratingID = ?", (id,)
            )

            if not targetRating:
                raise Exception(
                    "There were no ratings with that ID found!\n\nTry using the list command to narrow down your search."
                )

            packedRating = targetRating[0]
            oldMessageID = packedRating[8]
            createdByID = packedRating[1]
            invokedBy: discord.User = ctx.user

            if (createdByID != invokedBy.id) and not (
                await self.bot.is_owner(invokedBy)
            ):
                raise Exception(
                    f"That's not your rating!\n\nTo see a list of your ratings, use: `/albumrating list member member:@{invokedBy.name}`"
                )

            unpackedRating = music.unpackAlbumRating(self.bot, packedRating[-1])

            oldDate = unpackedRating.createdAt
            unpackedRating.createdAt = newDate

            finishedRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            oldMessageNotFoundWarning: str = ""

            if send_to_rating_channel:
                oldMessageReference = None

                try:
                    oldMessageReference = await ratingChannel.fetch_message(
                        oldMessageID
                    )
                except discord.errors.NotFound:
                    oldMessageNotFoundWarning = "\n\n⚠️WARN: The original message tied to this rating could not be found and edit_original_rating_message was set to True when this command was invoked. Instead of editing the message, a new one was sent and can be found through the link above."

                    pass

                if not oldMessageNotFoundWarning and edit_original_rating_message:
                    ratingMessageReference = await oldMessageReference.edit(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )
                else:
                    if oldMessageReference:
                        await oldMessageReference.delete()

                    ratingMessageReference = await ratingChannel.send(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link,
                        )
                    )
            else:
                finishedSentRating = await finishedRatingEmbed.send(ctx, ephemeral=True)

                try:
                    ratingMessageReference = await ratingChannel.fetch_message(
                        oldMessageID
                    )
                except discord.errors.NotFound:
                    ratingMessageReference = (
                        await finishedSentRating.original_response()
                    )
                    pass

            packedAlbumRating = unpackedRating.packAlbumRating(ratingMessageReference)

            database.setOne(
                """
                UPDATE `albumRatings` 
                SET createdAt = ?, lastRelatedMessage = ?, serializedRating = ?
                WHERE ratingID = ?
                """,
                (
                    packedAlbumRating[2],
                    packedAlbumRating[8],
                    packedAlbumRating[9],
                    id,
                ),
            )

            savedReply = EmbedReply(
                "Album Ratings - Change Date",
                "albumratings",
                description=f"Album rating date changed. ✅\n\nOld Date: {dates.formatSimpleDate(oldDate, discordDateFormat="f")}\nNew Date: {dates.formatSimpleDate(newDate, discordDateFormat="f")}\n\nView rating: {ratingMessageReference.jump_url}{oldMessageNotFoundWarning}",
            )

            await savedReply.send(ctx, ephemeral=True)
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

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
            database = LocalDatabase()

            targetRating = database.get(
                "SELECT * FROM albumRatings WHERE ratingID = ?", (id,)
            )

            if not targetRating:
                raise Exception(
                    "There were no ratings with that ID found!\n\nTry using the list command to narrow down your search."
                )

            packedRating = targetRating[0]
            oldMessageID = packedRating[8]
            createdByID = packedRating[1]
            invokedBy: discord.User = ctx.user

            if (createdByID != invokedBy.id) and not (
                await self.bot.is_owner(invokedBy)
            ):
                raise Exception(
                    f"That's not your rating!\n\nTo see a list of your ratings, use: `/albumrating list member member:@{invokedBy.name}`"
                )

            unpackedRating = music.unpackAlbumRating(self.bot, packedRating[-1])

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
                    oldMessageReference = await channel.fetch_message(oldMessageID)

                    await oldMessageReference.delete()
                except discord.errors.NotFound:
                    pass

            database.setOne("DELETE FROM albumRatings WHERE ratingID = ?", (id,))

            reply = EmbedReply(
                "Album Ratings - Deleted",
                "albumratings",
                description=f"Successfully deleted rating. ✅",
            )

            reply.add_field(
                name=prettyAlbumName, value=f"Rating ID: {unpackedRating.ratingID}"
            )

            await confirmationReply.edit_original_response(embed=reply, view=None)
        except Exception as e:
            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

    @albumRatings.command(
        description="Update the persistent buttons on all ratings. (OWNER ONLY)",
        guild_ids=[799341195109203998],
    )
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
        if await self.bot.is_owner(ctx.user):
            await ctx.defer()

            database = LocalDatabase()

            res = database.get("SELECT * FROM albumratings")

            for i in res:
                try:
                    ratingChannel = await self.bot.fetch_channel(RATING_CHANNEL)

                    targetMessage = await ratingChannel.fetch_message(i[-2])

                    await targetMessage.edit(
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            f"https://open.spotify.com/album/{i[6]}",
                        )
                    )

                    await asyncio.sleep(sleep_delay)
                except discord.NotFound:
                    pass
            
            reply = EmbedReply(
                "Album Ratings - Update Views",
                "albumratings",
                description="All ratings updated!"
            )

            await reply.send(ctx)
        else:
            reply = EmbedReply(
                "Album Ratings - Error",
                "albumratings",
                True,
                description="You cannot use this command!"
            )

            await reply.send(ctx)

def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
