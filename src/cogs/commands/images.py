import discord
import sys
from discord.ext import commands

from src.classes import *
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
        link: discord.Option(str, description="A direct link to an image."),  # type: ignore
        description: discord.Option(str, description="A description of the image.", required=True, min_length=MIN_IMAGE_DESCRIPTION_LENGTH, max_length=MAX_IMAGE_DESCRIPTION_LENGTH),  # type: ignore
        album: discord.Option(str, description="The album to add this image to. To create a new album, enter a string.", required=False, autocomplete=imagesCog.listAlbums),  # type: ignore
        keywords: discord.Option(str, description="A comma separated list of keywords used to search for this image. Ex: dovillio,gay", required=False),  # type: ignore
    ):
        await ctx.defer()

        try:
            linkIsImage = images.urlIsImage(link)

            if not linkIsImage:
                raise ValueError("That link was not an image! Try again.")

            database = LocalDatabase()

            keywordsSplit = keywords.split(",") if keywords else None

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

            reply = EmbedReply(
                "Images - Add Image",
                "images",
                description="Successfully added image into DB.",
            )

            reply.add_field(name=f"Image ID", value=newImageObj.id)

            imageEmbed = newImageObj.toEmbed()

            await ctx.followup.send(embeds=[reply, imageEmbed])
        except Exception as e:
            raise e
            reply = EmbedReply(
                "Images - Add - Error", "images", error=True, description=f"Error: {e}"
            )

            await reply.send(ctx)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
