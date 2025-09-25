import discord
import sys
from discord.ext import commands

from src.classes import *
from src.utils import music
from src.utils import dates

class SelectAlbum(discord.ui.Select):
    ISCOG = False

    def __init__(self, choices: list[tuple]):
        super().__init__(placeholder="Choose an album...", options=[discord.SelectOption(label=choice[1], value=str(choice[0])) for choice in choices])

    async def callback(self, ctx: discord.Interaction):
        self.view.choice = self.values[0]

        self.view.disable_all_items()
        self.view.stop()
        await ctx.response.edit_message(view=self.view)

class CancelButton(discord.ui.Button):
    ISCOG = False

    def __init__(self):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red, emoji="🛑")

    async def callback(self, ctx: discord.ApplicationContext):
        self.view.disable_all_items()
        self.view.stop()

        reply = EmbedReply(
            "Album Rating - Cancelled",
            "albumratings",
            True,
            description="Album rating cancelled."
        )
        
        await ctx.response.edit_message(view=self.view, embed=reply)

class ChooseAlbumView(discord.ui.View):
    ISCOG = False

    def __init__(self, choices: list[tuple]):
        super().__init__(timeout=60, disable_on_timeout=True)

        self.choice = None

        self.add_item(SelectAlbum(choices))
        self.add_item(CancelButton())

    async def on_timeout(self):
        self.disable_all_items()

        reply = EmbedReply(
            "Album Rating - Timed Out",
            "albumratings",
            True,
            description="Album rating timed out. Please retry."
        )

        if self.message:
            await self.message.edit(embed=reply, view=self)

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
            
            reply = EmbedReply(
                "Album Rating - Choose Album",
                "albumratings",
                description="Choose the album you wish to rate from the Spotify results below."
            )

            reply.set_footer(text="Album data provided by Spotify®.", icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png")
            
            cleanedChoices = []

            for idx, album in enumerate(albumQueryResults["albums"]["items"]):
                artists = ", ".join([artist["name"] for artist in album["artists"]])

                releaseYear = (dates.simpleDateObj(album["release_date"])).year
                
                choice = f"{album['name']} - {artists} - {releaseYear}"

                id = album["id"]

                cleanedChoices.append((idx, choice, id))
                reply.add_field(name=f"{idx + 1}. {album['name']} · {releaseYear}", value=artists, inline=False)

            view = ChooseAlbumView(cleanedChoices)

            msg = await ctx.respond(embed=reply, view=view, ephemeral=True)
            view.message = await msg.original_response()
            
            await view.wait()

            if view.choice == None:
                return

            choiceIdx = int(view.choice)

            choiceID = cleanedChoices[choiceIdx][2]

            albumDetailsFromID = music.fetchAlbumDetailsByID(choiceID)

            parsedAlbumDetails: music.Album = music.parseAlbumDetails(albumDetailsFromID, ctx.user.id)

            reply = EmbedReply(
                f"Album Rating - {parsedAlbumDetails.name} 🔗",
                "albumratings",
                url=parsedAlbumDetails.link,
                description="\n\n"
            )
            
            if parsedAlbumDetails.coverImage:
                reply.set_thumbnail(url=parsedAlbumDetails.coverImage)

                reply.colour = parsedAlbumDetails.coverImageColour

            for track in parsedAlbumDetails.tracks:
                reply.description += f"**{track.trackNumber}.** {track.name} · `{track.getRating(True)}`\n"

            reply.add_field(name="***Overall Rating***", value=parsedAlbumDetails.meanRating(True), inline=True)
            reply.add_field(name="***Comments***", value=parsedAlbumDetails.parseComments(), inline=True)

            reply.set_footer(text=f"Album data provided by Spotify®. · Rating ID: {parsedAlbumDetails.ratingID}", icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green-300x300.png")

            await reply.send(ctx)
            
        except Exception as e:
            raise e
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
