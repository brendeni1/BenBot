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

                id = album["id"]

                cleanedChoices.append((idx, album['name'], artists, releaseYear, id))
                reply.add_field(name=f"{idx + 1}. {album['name']} · {releaseYear}", value=artists, inline=False)

            view = music.ChooseAlbumView(cleanedChoices)

            msg = await ctx.respond(embed=reply, view=view, ephemeral=True)
            view.message = await msg.original_response()

            await view.wait()

            if view.choice == None:
                return

            albumDetailsFromID = music.fetchAlbumDetailsByID(view.choice)

            parsedAlbumDetails: music.Album = music.parseAlbumDetails(albumDetailsFromID, ctx.user)

            # start at first track
            firstTrack = parsedAlbumDetails.tracks[0]

            view = music.SongRatingView(parsedAlbumDetails)

            wholeAlbumEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)
            songRatingEmbed = music.TrackRatingEmbedReply(firstTrack)

            view.message = await ctx.respond(
                embeds=[wholeAlbumEmbed, songRatingEmbed], view=view, ephemeral=True
            )

            timedOut = await view.wait()

            if timedOut or view.cancelled:
                view.disable_all_items()

                return

            wholeAlbumEmbed = music.AlbumRatingEmbedReply(parsedAlbumDetails)

            await wholeAlbumEmbed.send(ctx, False)
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
