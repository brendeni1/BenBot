import discord
import random
import sys
from discord.ext import commands

from src.classes import *
from src import constants
from src.utils import imagesCog, images, text, dates

MIN_IMAGE_DESCRIPTION_LENGTH = 2
MAX_IMAGE_DESCRIPTION_LENGTH = 3500


class ImageCommands(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for interacting with images in the bot."

    imageCommands = discord.SlashCommandGroup(
        name="images",
        description="Commands for interacting with images in the bot.",
        guild_ids=[799341195109203998],
    )

    @imageCommands.command(
        description="Add an image to the bot's DB.", guild_ids=[799341195109203998]
    )
    async def add(
        self,
        ctx: discord.ApplicationContext,
        image_attachment: discord.Option(discord.Attachment, description="Upload an image file.", required=False),  # type: ignore
        image_link: discord.Option(str, description="A direct link to an image instead of uploading.", required=False, max_length=512),  # type: ignore
        description: discord.Option(str, description="A description of the image.", required=False, min_length=MIN_IMAGE_DESCRIPTION_LENGTH, max_length=MAX_IMAGE_DESCRIPTION_LENGTH),  # type: ignore
        album: discord.Option(str, description="The album to add this image to. To create a new album, enter a string.", required=False, autocomplete=imagesCog.listAlbums),  # type: ignore
        keywords: discord.Option(str, description="A comma separated list of keywords used to search for this image. Ex: dovillio,gay", required=False),  # type: ignore
    ):
        await ctx.defer()

        if image_attachment:
            # Send the file to a permanent storage channel
            storage_channel = self.bot.get_channel(constants.STORAGE_CHANNEL_ID)
            # Re-upload the file to get a "permanent" link
            permanent_msg = await storage_channel.send(
                file=await image_attachment.to_file()
            )
            link = permanent_msg.attachments[0].url
        elif image_link:
            link = image_link

        # 2. Validation
        if not link:
            reply = EmbedReply(
                "Images - Add - Error",
                "images",
                error=True,
                description="You must provide either an image link OR an attachment.",
            )
            await reply.send(ctx)
            return

        try:
            linkIsImage = images.urlIsImage(link)

            if not linkIsImage:
                raise ValueError(
                    "The provided source was not a valid image! Try again."
                )

            database = LocalDatabase()
            keywordsSplit = keywords.split(",") if keywords else None

            # 3. Check for duplicates
            duplicateImage = database.get(
                query="SELECT * FROM images WHERE link = ?", params=(link,), limit=1
            )

            if duplicateImage:
                duplicateImageObj = imagesCog.dbToObj(duplicateImage[0])

                reply = EmbedReply(
                    "Images - Add - Error",
                    "images",
                    error=True,
                    description=f"That [image]({duplicateImageObj.link}) was already added by <@{duplicateImageObj.createdBy}> with ID: `{duplicateImageObj.id}`",
                )

                reply.set_image(url=duplicateImageObj.link)
                await reply.send(ctx)
                return

            # 4. Create and Write Object
            newImageObj = imagesCog.ImageEntry(
                id=text.generateUUID(),
                timestamp=dates.simpleDateObj(timeNow=True),
                album=album.lower() if album else None,
                link=link,
                description=description,
                keywords=keywordsSplit,
                createdBy=ctx.user.id,
            )

            newImageObj.writeToDB()

            # 5. Success UI
            reply = EmbedReply(
                "Images - Add Image",
                "images",
                description="Successfully added image into DB.",
            )

            reply.add_field(name=f"Image ID", value=newImageObj.id)

            imageEmbed = newImageObj.toEmbed()
            imageView = imagesCog.ImageView(newImageObj)

            await ctx.followup.send(embeds=[reply, imageEmbed], view=imageView)

        except Exception as e:
            reply = EmbedReply(
                "Images - Add - Error", "images", error=True, description=f"Error: {e}"
            )
            await reply.send(ctx)

    @imageCommands.command(
        description="Delete an image in the bot's DB.", guild_ids=[799341195109203998]
    )
    async def delete(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(str, description="Can be either an ID or the link associated with the image."),  # type: ignore
    ):
        await ctx.defer()

        try:
            db = LocalDatabase()

            sql = "SELECT * FROM images WHERE id = ? OR link = ?"
            params = (query, query)

            results = db.get(sql, params)

            if not results:
                raise Exception(
                    "There were no images found with that ID or image link!"
                )

            result = imagesCog.dbToObj(results[0])

            sql = "DELETE FROM images WHERE id = ? OR link = ?"

            db.query(sql, params)

            newEmbed = EmbedReply(
                "Images - Delete",
                "images",
                description=f"Successfully deleted [image]({result.link}) with ID `{result.id}` from the DB.",
            )

            await newEmbed.send(ctx)
        except Exception as e:
            # raise e
            reply = EmbedReply(
                "Images - Delete - Error",
                "images",
                error=True,
                description=f"Error: {e}",
            )

            await reply.send(ctx)

    @imageCommands.command(
        description="View an image in the bot's DB.", guild_ids=[799341195109203998]
    )
    async def search(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(str, description="Can be either an ID or the link associated with the image, or a keyword/album/description term."),  # type: ignore
    ):
        await ctx.defer()

        try:
            db = LocalDatabase()

            # Search by ID, Link, Album (Partial), or Keywords (Partial)
            sql = """
                SELECT * FROM images 
                WHERE id = ? 
                OR link = ? 
                OR album LIKE ? 
                OR keywords LIKE ?
                OR description LIKE ?
            """

            wildcard_query = f"%{query}%"
            params = (query, query, wildcard_query, wildcard_query, wildcard_query)

            results = db.get(sql, params)

            if not results:
                reply = EmbedReply(
                    "Images - Search - Error",
                    "images",
                    error=True,
                    description=f"No images found matching: `{query}`",
                )
                await reply.send(ctx)
                return

            # Convert all DB results to ImageEntry objects
            image_objs = [imagesCog.dbToObj(res) for res in results]

            # Create the View with the results list
            # We default to showing the first result (index 0)
            view = imagesCog.ImageSearchView(image_objs, current_index=0)

            # Create the Embed for the first result
            embed = image_objs[0].toEmbed()

            await ctx.followup.send(embed=embed, view=view)

        except Exception as e:
            reply = EmbedReply(
                "Images - Search - Error",
                "images",
                error=True,
                description=f"Error: {e}",
            )
            await reply.send(ctx)

    @imageCommands.command(
        description="Send a persistent view of a specific image by ID or Link.",
        guild_ids=[799341195109203998],
    )
    async def view(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(str, description="The ID or Link of the image to view."),  # type: ignore
    ):
        await ctx.defer()

        try:
            db = LocalDatabase()

            # Exact match on ID or Link (same logic as Delete)
            sql = "SELECT * FROM images WHERE id = ? OR link = ?"
            params = (query, query)

            results = db.get(sql, params)

            if not results:
                reply = EmbedReply(
                    "Images - View - Error",
                    "images",
                    error=True,
                    description=f"No image found with ID or Link matching: `{query}`",
                )
                await reply.send(ctx)
                return

            # Convert result to Object
            imageObj = imagesCog.dbToObj(results[0])

            # Create the standard View
            # We use ImageView directly (not ImageSearchView) because it defaults to timeout=None
            # and does not have the select menu complexity.
            view = imagesCog.ImageView(imageObj)

            # Generate the embed
            embed = imageObj.toEmbed()

            await ctx.followup.send(embed=embed, view=view)

        except Exception as e:
            reply = EmbedReply(
                "Images - View - Error",
                "images",
                error=True,
                description=f"Error: {e}",
            )
            await reply.send(ctx)

    @imageCommands.command(
        description="Send a persistent view of a random image, optionally with an album.",
        guild_ids=[799341195109203998],
    )
    async def random(
        self,
        ctx: discord.ApplicationContext,
        album: discord.Option(str, description="The album to pull from.", required=False, autocomplete=imagesCog.listAlbums),  # type: ignore
    ):
        await ctx.defer()

        try:
            db = LocalDatabase()

            # Exact match on ID or Link (same logic as Delete)
            sql = "SELECT * FROM images"
            params = ()

            if album:
                sql += " WHERE album LIKE ?"
                params = (f"%{album}%",)

            results = db.get(sql, params)

            if not results and album:
                reply = EmbedReply(
                    "Images - Random - Error",
                    "images",
                    error=True,
                    description=f"No image found in the album: `{album}`",
                )
                await reply.send(ctx)
                return
            elif not results and not album:
                reply = EmbedReply(
                    "Images - Random - Error",
                    "images",
                    error=True,
                    description=f"No images found in the DB!",
                )
                await reply.send(ctx)
                return

            # Convert result to Object
            imageObj = imagesCog.dbToObj(random.choice(results))

            # Create the standard View
            # We use ImageView directly (not ImageSearchView) because it defaults to timeout=None
            # and does not have the select menu complexity.
            view = imagesCog.ImageView(imageObj)

            # Generate the embed
            embed = imageObj.toEmbed("Images - Random 🔗↗️")

            await ctx.followup.send(embed=embed, view=view)

        except Exception as e:
            reply = EmbedReply(
                "Images - Random - Error",
                "images",
                error=True,
                description=f"Error: {e}",
            )
            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
