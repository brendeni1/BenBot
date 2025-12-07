import discord
import datetime

from src.utils.logging import logClasses
from src.utils import dates

from src.classes import *


class CommandLogEntry(logClasses.LogEntry):
    def __init__(
        self,
        *,
        customID: str = None,
        customTimestamp: datetime.datetime = None,
        qualifiedCommandName: str,
        invocationGuildID: int = None,
        invocationGuildName: str,
        invocationChannelID: int = None,
        invocationChannelName: str,
        invocationUserID: int,
        invocationOptions: list[dict] = None,
    ):
        super().__init__(customID=customID, customTimestamp=customTimestamp)

        self.qualifiedCommandName = qualifiedCommandName
        self.invocationGuildID = invocationGuildID
        self.invocationGuildName = invocationGuildName
        self.invocationChannelID = invocationChannelID
        self.invocationChannelName = invocationChannelName
        self.invocationUserID = invocationUserID
        self.invocationOptions = invocationOptions


def flattenCommandOptions(
    options: list[dict], string: bool = True
) -> dict[str, str] | str | None:
    if not options:
        return

    flattenedOptions = {}

    for option in options:
        flattenedOptions[option["name"]] = str(option["value"])

    return str(flattenedOptions) if string else flattenedOptions


async def contextToLogEntry(
    ctx: discord.ApplicationContext,
) -> CommandLogEntry:
    qualifiedCommandName = ctx.command.qualified_name
    guildID = ctx.guild_id
    guildName = ctx.guild.name if ctx.guild else "DM"
    channelID = ctx.channel_id
    channelName = ctx.channel.name if ctx.guild else "DM"
    userID = ctx.user.id

    flattenedOptions = flattenCommandOptions(ctx.selected_options, string=True)

    entryObj = CommandLogEntry(
        qualifiedCommandName=qualifiedCommandName,
        invocationGuildID=guildID,
        invocationGuildName=guildName,
        invocationChannelID=channelID,
        invocationChannelName=channelName,
        invocationUserID=userID,
        invocationOptions=flattenedOptions,
    )

    return entryObj


def insertLogEntry(entry: CommandLogEntry):
    database = LocalDatabase(database="logs")

    sql = """
    INSERT INTO commands 
    (entryID, timestamp, qualifiedCommandName, invocationGuildID, invocationGuildName, invocationChannelID, invocationChannelName, invocationUserID, invocationOptions) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        entry.id,
        dates.formatSimpleDate(entry.timestamp, databaseDate=True),
        entry.qualifiedCommandName,
        entry.invocationGuildID,
        entry.invocationGuildName,
        entry.invocationChannelID,
        entry.invocationChannelName,
        entry.invocationUserID,
        entry.invocationOptions,
    )

    database.setOne(sql, params)
