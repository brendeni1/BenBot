import discord
import requests
import asyncio
import sys
from discord.ext import commands, pages

from src.classes import *
from src.utils import music
from src.utils import dates

RATING_CHANNEL = 946507420916678688

DELETE_SAVED_REPLY_AFTER = 15

ALBUM_APISEARCH_RESULTS_LIMIT = 5

def paginateRatingList(
    results: list[tuple], title: str, description: str
) -> list[pages.Page]:
    pageList = []

    for chunk in range(0, len(results), 25):
        page = EmbedReply(title, "albumratings", description=description)

        for result in results[chunk : chunk + 25]:
            formattedCreatedAt = dates.formatSimpleDate(
                result[2], discordDateFormat="d"
            )

            formattedRatingName = text.truncateString(
                f"{result[5]} · {result[4]} · {formattedCreatedAt}", 256
            )[0]

            page.add_field(
                name=formattedRatingName, value=f"Rating ID: {result[0]}", inline=False
            )

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
    ):
        attempt = 0
        maxRetries = 2
        
        while attempt < maxRetries:
            try:
                albumQueryResults = music.searchForAlbumName(album_name, limit=ALBUM_APISEARCH_RESULTS_LIMIT)

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

                cleanedChoices = []

                for idx, album in enumerate(albumQueryResults["albums"]["items"]):
                    artists = ", ".join([artist["name"] for artist in album["artists"]])

                    releaseYear = (dates.simpleDateObj(album["release_date"])).year

                    id = album["id"]

                    cleanedChoices.append((idx, album["name"], artists, releaseYear, id))
                    reply.add_field(
                        name=f"{idx + 1}. {album['name']} · {releaseYear}",
                        value=artists,
                        inline=False,
                    )

                view = music.ChooseAlbumView(cleanedChoices)

                msg = await ctx.respond(embed=reply, view=view, ephemeral=True)
                view.message = await msg.original_response()

                await view.wait()

                if view.choice == None:
                    return
                
                await msg.delete_original_response()

                albumDetailsFromID = music.fetchAlbumDetailsByID(view.choice)

                parsedAlbumDetails: music.Album = music.parseAlbumDetails(
                    albumDetailsFromID, ctx.user
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

                ratingChannel = self.bot.get_channel(RATING_CHANNEL)

                if not ratingChannel:
                    ratingChannel = ctx.channel

                displayedAlbumReviewMessage: discord.Message = await ratingChannel.send(
                    embed=finishedRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        parsedAlbumDetails.link
                    ),
                )

                packedAlbumRating = parsedAlbumDetails.packAlbumRating(
                    displayedAlbumReviewMessage
                )

                database = LocalDatabase()

                database.setOne(
                    """
                    INSERT INTO `albumRatings` 
                    (`ratingID`, `createdBy`, `createdAt`, `editedAt`, `ratingArtist`, `ratingAlbum`, `formattedRating`, `lastRelatedMessage`, `serializedRating`) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    packedAlbumRating,
                )

                await originalResponse.delete()

                savedReply = EmbedReply(
                    "Album Ratings - Saved",
                    "albumratings",
                    description=f"Album rating saved. ✅\n\nView rating: {displayedAlbumReviewMessage.jump_url}\n\n(This message will delete after {DELETE_SAVED_REPLY_AFTER} seconds.)",
                )

                await ctx.send(
                    content=ctx.author.mention,
                    embed=savedReply,
                    delete_after=DELETE_SAVED_REPLY_AFTER
                )

                break
            except requests.exceptions.ConnectionError:
                attempt += 1

                await asyncio.sleep(1)
                
                continue
            except Exception as e:
                print(e)

                reply = EmbedReply(
                    "Album Ratings - Error", "albumratings", True, description=str(e)
                )

                await reply.send(ctx, ephemeral=True)

                break
        else:
            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description="The Spotify API seems to be having issues right now.\n\nPlease try again later."
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
            oldMessageID = packedRating[7]

            unpackedRating = music.unpackAlbumRating(self.bot, packedRating[-1])

            albumRatingEmbed = music.AlbumRatingEmbedReply(unpackedRating)

            if send_to_rating_channel:
                channel = self.bot.get_channel(RATING_CHANNEL)

                if not channel:
                    raise Exception(
                        "The rating channel could not be found.\n\nSet send_to_rating_channel=False when using this command."
                    )

                try:
                    oldMessageReference = await channel.fetch_message(oldMessageID)

                    await oldMessageReference.delete()
                except discord.errors.NotFound:
                    pass

                ratingMessageReference = await channel.send(
                    embed=albumRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                        unpackedRating.link
                    ),
                )

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
            print(e)

            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

    list_ratings = albumRatings.create_subgroup(
        "list",
        "Use these commands to list ratings based on metrics.",
        guild_ids=[799341195109203998],
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

            pageList = paginateRatingList(
                results,
                "Album Ratings - List By Member",
                f"List of ratings for {member.mention}. ({len(results)} Total)",
            )

            pagignator = pages.Paginator(
                pages=pageList,
            )

            await pagignator.respond(ctx.interaction, ephemeral=True)
        except Exception as e:
            print(e)

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
            oldMessageID = packedRating[7]
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

            originalResponse: discord.Interaction = await ctx.respond(
                embeds=[wholeAlbumEmbed, songRatingEmbed], view=view
            )
            view.message = originalResponse

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
                            unpackedRating.link
                        ),
                    )
                else:
                    if oldMessageReference:
                        await oldMessageReference.delete()

                    ratingMessageReference = await ratingChannel.send(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link
                        )
                    )

                packedAlbumRating = unpackedRating.packAlbumRating(
                    ratingMessageReference
                )

                database.setOne(
                    """
                    UPDATE `albumRatings` 
                    SET editedAt = ?, ratingArtist = ?, ratingAlbum = ?, formattedRating = ?, lastRelatedMessage = ?, serializedRating = ?
                    WHERE ratingID = ?
                    """,
                    (
                        packedAlbumRating[3],
                        packedAlbumRating[4],
                        packedAlbumRating[5],
                        packedAlbumRating[6],
                        packedAlbumRating[7],
                        packedAlbumRating[8],
                        id,
                    ),
                )

                await originalResponse.delete_original_response()

                savedReply = EmbedReply(
                    "Album Ratings - Edited",
                    "albumratings",
                    description=f"Album rating edited. ✅\n\nView rating: {ratingMessageReference.jump_url}{oldMessageNotFoundWarning}\n\n(This message will delete after {DELETE_SAVED_REPLY_AFTER} seconds.)",
                )

                await ctx.send(
                    content=ctx.author.mention,
                    embed=savedReply,
                    delete_after=DELETE_SAVED_REPLY_AFTER
                )
            else:
                await originalResponse.edit(
                    embed=finishedRatingEmbed,
                    view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link
                    )
                )

                packedAlbumRating = unpackedRating.packAlbumRating(originalResponse)

                database.setOne(
                    """
                    UPDATE `albumRatings` 
                    SET editedAt = ?, ratingArtist = ?, ratingAlbum = ?, formattedRating = ?, serializedRating = ?
                    WHERE ratingID = ?
                    """,
                    (
                        packedAlbumRating[3],
                        packedAlbumRating[4],
                        packedAlbumRating[5],
                        packedAlbumRating[6],
                        packedAlbumRating[8],
                        id,
                    ),
                )
        except Exception as e:
            print(e)

            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)

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

            if not ratingChannel and (edit_original_rating_message or send_to_rating_channel):
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
            oldMessageID = packedRating[7]
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
                            unpackedRating.link
                        ),
                    )
                else:
                    if oldMessageReference:
                        await oldMessageReference.delete()

                    ratingMessageReference = await ratingChannel.send(
                        embed=finishedRatingEmbed,
                        view=music.FinishedRatingPersistentMessageButtonsView(
                            unpackedRating.link
                        ),
                    )
            else:
                finishedSentRating = await finishedRatingEmbed.send(
                    ctx,
                    ephemeral=True
                )

                try:
                    ratingMessageReference = await ratingChannel.fetch_message(
                        oldMessageID
                    )
                except discord.errors.NotFound:
                    ratingMessageReference = await finishedSentRating.original_response()
                    pass

            packedAlbumRating = unpackedRating.packAlbumRating(
                ratingMessageReference
            )

            database.setOne(
                """
                UPDATE `albumRatings` 
                SET createdAt = ?, ratingArtist = ?, ratingAlbum = ?, formattedRating = ?, lastRelatedMessage = ?, serializedRating = ?
                WHERE ratingID = ?
                """,
                (
                    packedAlbumRating[2],
                    packedAlbumRating[4],
                    packedAlbumRating[5],
                    packedAlbumRating[6],
                    packedAlbumRating[7],
                    packedAlbumRating[8],
                    id,
                ),
            )

            savedReply = EmbedReply(
                "Album Ratings - Change Date",
                "albumratings",
                description=f"Album rating date changed. ✅\n\nOld Date: {dates.formatSimpleDate(oldDate, discordDateFormat="f")}\nNew Date: {dates.formatSimpleDate(newDate, discordDateFormat="f")}\n\nView rating: {ratingMessageReference.jump_url}{oldMessageNotFoundWarning}",
            )

            await savedReply.send(
                ctx,
                ephemeral=True
            )
        except Exception as e:
            print(e)

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
            oldMessageID = packedRating[7]
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
                "Album Ratings - Delete",
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
                    "Album Ratings - Delete",
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
                "Album Ratings - View ID",
                "albumratings",
                description=f"Successfully deleted rating. ✅",
            )

            reply.add_field(
                name=prettyAlbumName, value=f"Rating ID: {unpackedRating.ratingID}"
            )

            await confirmationReply.edit_original_response(embed=reply, view=None)
        except Exception as e:
            print(e)

            reply = EmbedReply(
                "Album Ratings - Error", "albumratings", True, description=str(e)
            )

            await reply.send(ctx, ephemeral=True)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
