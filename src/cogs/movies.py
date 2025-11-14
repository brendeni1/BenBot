import discord
import datetime
import sys
from discord.ext import commands

from src.classes import *

from src import constants

from src.utils import movies
from src.utils import dates

DEFAULT_CHAIN = "Landmark"
DEFAULT_PROVINCE = "ON"
DEFAULT_LOCATION = "7802"  # Windsor

SHOWTIME_DATE_QUERY_LIMIT = 3

SHOWTIME_DATE_SELECT_RANGE = 14


async def chainAutocomplete(ctx):
    query = ctx.value.lower()

    # empty input? show defaults
    if query == "":
        return list(constants.MOVIE_CINEMAS.keys())[:25]

    return [chain for chain in constants.MOVIE_CINEMAS if query in chain.lower()][:25]


async def provinceAutocomplete(ctx: discord.AutocompleteContext):
    selectedChain = ctx.options.get("chain")

    provinces = list(constants.MOVIE_CINEMAS[selectedChain].keys())
    query = ctx.value.lower()

    return [province for province in provinces if query in province.lower()][:25]


async def locationAutocomplete(ctx: discord.AutocompleteContext):
    chain = ctx.options.get("chain")
    province = ctx.options.get("province")

    if not chain or chain not in constants.MOVIE_CINEMAS:
        return []

    if not province or province not in constants.MOVIE_CINEMAS[chain]:
        return []

    query = ctx.value.lower()

    return [
        discord.OptionChoice(name=item["location"], value=item["id"])
        for item in constants.MOVIE_CINEMAS[chain][province]
        if query in item["location"].lower()
    ][:25]


async def startDateAutocomplete(ctx: discord.AutocompleteContext):
    now = datetime.date.today()

    deltaToEnd = datetime.timedelta(days=SHOWTIME_DATE_SELECT_RANGE)

    end = now + deltaToEnd

    nowToEndRange = dates.dateRange(now, end)

    formattedNowToEndRange = [
        discord.OptionChoice(
            name=(
                "Today"
                if date == now
                else (
                    "Tomorrow"
                    if date == now + datetime.timedelta(days=1)
                    else dates.formatSimpleDate(date)
                )
            ),
            value=date.isoformat(),
        )
        for date in nowToEndRange
    ]

    return formattedNowToEndRange[:25]


class Movies(commands.Cog):
    ISCOG = True

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.description = "Commands for looking up movies and showtimes."

    movies = discord.SlashCommandGroup(
        name="movies",
        description="Commands for looking up details about movies.",
        guild_ids=[799341195109203998],
    )

    @movies.command(
        description="View upcoming showtimes for movies.",
        guild_ids=[799341195109203998],
    )
    async def showtimes(
        self,
        ctx: discord.ApplicationContext,
        start_date: discord.Option(
            input_type=str,
            description="Date to start looking for showtimes on.",
            autocomplete=startDateAutocomplete,
            required=False,
        ),  # type: ignore
        chain: discord.Option(
            input_type=str,
            description="Select which chain of cinema to use.",
            autocomplete=chainAutocomplete,
            required=False,
        ),  # type: ignore
        province: discord.Option(
            input_type=str,
            description="Select which province to look up cinemas.",
            autocomplete=provinceAutocomplete,
            required=False,
        ),  # type: ignore
        location: discord.Option(
            input_type=str,
            description="Select which cinema location to view.",
            autocomplete=locationAutocomplete,
            required=False,
        ),  # type: ignore
    ):
        try:
            if any([chain, province, location]):
                if not all([chain, province, location]):
                    raise Exception(
                        "If setting `chain`, `province`, or `location` manually, you must set all 3 explicitly!"
                    )

            chain = chain or DEFAULT_CHAIN
            province = province or DEFAULT_PROVINCE
            location = location or DEFAULT_LOCATION

            start_date = (
                dates.simpleDateObj(start_date) or datetime.date.today()
            ).date()

            await ctx.respond(
                f"You picked **{chain} → {province} → {location}** for start date {dates.formatSimpleDate(start_date)}"
            )
        except Exception as e:
            reply = EmbedReply(
                "Movie Showtimes - Error", "movies", True, description=f"Error: {e}"
            )

            await reply.send(ctx, ephemeral=True)


def setup(bot):
    currentFile = sys.modules[__name__]

    for name in dir(currentFile):
        obj = getattr(currentFile, name)

        if isinstance(obj, type) and obj.__module__ == currentFile.__name__:
            if obj.ISCOG:
                bot.add_cog(obj(bot))
