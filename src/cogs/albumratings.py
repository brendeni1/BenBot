import discord
import sys
from discord.ext import commands

from src.classes import *
from src.utils import music
from src.utils import dates

class AlbumRatings(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for creating an album rating."

    albumRatings = discord.SlashCommandGroup("albumrating", "A collection of commands for rating albums.", guild_ids=[799341195109203998])

    @albumRatings.command(description = "Create an album rating.", guild_ids=[799341195109203998])
    async def create(
        self,
        ctx: discord.ApplicationContext,
        album_name: discord.Option(
            str,
            description="Provide the name of the album. The album must exist on Spotify.",
            required=True
        ) # type: ignore
        ):

        try:
            albumQueryResults = music.searchForAlbumName(album_name)

            if not albumQueryResults["albums"]["items"]:
                raise Exception("No albums were found with that name!")
            
            cleanedChoices = []

            for idx, album in enumerate(albumQueryResults["albums"]["items"]):
                artists = ", ".join([artist["name"] for artist in album["artists"]])

                releaseYear = (dates.simpleDateObj(album["release_date"])).year
                
                choice = f"{album['name']} - {artists} - {releaseYear}"

                id = album["id"]

                cleanedChoices.append((idx, choice, id))

            reply = EmbedReply(
                "Album Rating - Choose Album",
                "albumratings",
                description="Choose the correct album from the Spotify results below...\n"
            )

            for choice in cleanedChoices:
                reply.description += f"\n{choice[0] + 1}. {choice[1]}"

            await reply.send(ctx)

        except Exception as e:
            reply = EmbedReply(
                "Album Rating - Error",
                "albumratings",
                True,
                description=e
            )

            await reply.send(ctx, ephemeral=True)


def setup(bot):
    currentFile = sys.modules[__name__]
    
    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
