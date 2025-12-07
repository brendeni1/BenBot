import discord
import datetime

from src.utils.logging import logClasses
from src.utils import dates

from src.classes import *


def flattenCommandOptions(
    options: list[dict], string: bool = True
) -> dict[str, str] | str | None:
    if not options:
        return

    flattenedOptions = {}

    for option in options:
        flattenedOptions[option["name"]] = str(option["value"])

    return str(flattenedOptions) if string else flattenedOptions


def contextToLogEntry(
    ctx: discord.ApplicationContext,
) -> logClasses.CommandLogEntry:
    qualifiedCommandName = ctx.command.qualified_name
    guildID = ctx.guild_id
    guildName = ctx.guild.name if ctx.guild else "DM"
    channelID = ctx.channel_id
    channelName = ctx.channel.name if ctx.guild else "DM"
    userID = ctx.user.id

    flattenedOptions = flattenCommandOptions(ctx.selected_options, string=True)

    entryObj = logClasses.CommandLogEntry(
        qualifiedCommandName=qualifiedCommandName,
        invocationGuildID=guildID,
        invocationGuildName=guildName,
        invocationChannelID=channelID,
        invocationChannelName=channelName,
        invocationUserID=userID,
        invocationOptions=flattenedOptions,
    )

    return entryObj


def dbResultToLogEntry(
    result: tuple,
) -> logClasses.CommandLogEntry:
    entryID = result[0]
    entryTimestamp = dates.simpleDateObj(result[1])
    qualifiedCommandName = result[2]
    guildID = result[3]
    guildName = result[4]
    channelID = result[5]
    channelName = result[6]
    userID = result[7]

    options = result[8]

    entryObj = logClasses.CommandLogEntry(
        customID=entryID,
        customTimestamp=entryTimestamp,
        qualifiedCommandName=qualifiedCommandName,
        invocationGuildID=guildID,
        invocationGuildName=guildName,
        invocationChannelID=channelID,
        invocationChannelName=channelName,
        invocationUserID=userID,
        invocationOptions=options,
    )

    return entryObj


def insertLogEntry(entry: logClasses.CommandLogEntry):
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
