import discord
import datetime
import pickle

from src.utils.logging import logClasses
from src.utils import dates

from src.classes import *


def unserializeAttachment(target: bytes) -> logClasses.SmallDiscordAttachment:
    unserialized = pickle.loads(target)

    return unserialized


def attachmentToSmallAttachmentObj(
    attachment: discord.Attachment,
) -> logClasses.SmallDiscordAttachment:
    discordID = attachment.id
    sizeBytes = attachment.size
    fileName = attachment.filename
    link = attachment.url
    description = attachment.description
    mediaType = attachment.content_type
    height = attachment.height
    width = attachment.width

    smallAttachmentObj: logClasses.SmallDiscordAttachment = (
        logClasses.SmallDiscordAttachment(
            discordID=discordID,
            sizeBytes=sizeBytes,
            fileName=fileName,
            link=link,
            description=description,
            mediaType=mediaType,
            height=height,
            width=width,
        )
    )

    return smallAttachmentObj


def messageToLogEntryObj(
    message: discord.Message, bot: discord.Bot
) -> logClasses.MessageLogEntry:
    messageTypes: list[str] = []
    discordMessageID = message.id
    guildID = message.guild.id if message.guild else None
    channelID = message.channel.id

    rawChannel = message.channel

    guildName = "Unknown"
    channelName = None

    if isinstance(rawChannel, discord.DMChannel):
        if rawChannel.recipient:
            channelName = f"DM with @{rawChannel.recipient.name}"
            guildName = "DM"

            messageTypes.append("dm")
        else:
            guildName = "Ephemeral Message"
            channelName = "Ephemeral Message"

            messageTypes.append("ephemeral")
    else:
        try:
            channelName = rawChannel.name
            guildName = message.guild.name
        except AttributeError:
            pass

    userID = message.author.id
    userName = message.author.name
    userNickname = message.author.global_name
    isBot = message.author.bot
    systemContent = message.system_content if message.system_content else None
    content = message.clean_content if message.clean_content else None

    wordCount = len(content.split(" ")) if content else 0

    attachments: list[logClasses.SmallDiscordAttachment] = []

    if content:
        messageTypes.append("text")

    if message.embeds:
        messageTypes.append("embeds")

    if message.thread:
        messageTypes.append("thread")

    if message.activity:
        messageTypes.append("activity")

    if message.application:
        messageTypes.append("application")

    if message.call:
        messageTypes.append("call")

    if message.tts:
        messageTypes.append("tts")

    if message.components:
        messageTypes.append("components")

    if (bot.user.id == message.author.id) and (not content) and (not messageTypes):
        messageTypes.append("deferred")

    for attachment in message.attachments:
        smallAttachmentObj = attachmentToSmallAttachmentObj(attachment)

        attachments.append(smallAttachmentObj)

        if smallAttachmentObj.mediaType:
            messageTypes.append(smallAttachmentObj.mediaType)

    logEntryObj = logClasses.MessageLogEntry(
        discordMessageID=discordMessageID,
        guildID=guildID,
        guildName=guildName,
        channelID=channelID,
        channelName=channelName,
        userID=userID,
        userName=userName,
        userNickname=userNickname,
        isBot=isBot,
        wordCount=wordCount,
        systemContent=systemContent,
        content=content,
        attachments=attachments,
        messageTypes=messageTypes,
    )

    return logEntryObj


def dbResultToLogEntry(
    dbResult: tuple,
    columnOrder: list[str] = [
        "entryID",
        "discordMessageID",
        "timestamp",
        "messageTypes",
        "guildID",
        "guildName",
        "channelID",
        "channelName",
        "userID",
        "userName",
        "userNickname",
        "content",
        "systemContent",
        "attachments",
        "isBot",
        "wordCount",
    ],
) -> logClasses.MessageLogEntry:
    """
    Converts a single database row result (tuple) back into a MessageLogEntry object.

    :param dbResult: A tuple representing one row from the 'messages' SQL table.
    :param columnOrder: The order of columns in the SQL query result.
    :return: A fully instantiated MessageLogEntry object.
    """

    # Map the result tuple to column names for easy access
    data = dict(zip(columnOrder, dbResult))

    # --- Deserialization/Parsing Steps ---

    # 1. Deserialize timestamp (string -> datetime)
    # The string format is 'YYYY-MM-DD HH:MM:SS', which formatSimpleDate's reverse should handle.
    timestamp_obj = dates.simpleDateObj(data["timestamp"])

    try:
        rawMessageTypes = data["messageTypes"]

        message_types_list = rawMessageTypes.split(",")
    except:
        # Fallback if the string is empty or invalid
        message_types_list = []

    # 3. Deserialize attachments (BLOB/bytes -> list[SmallDiscordAttachment])
    attachments_blob = data["attachments"]
    attachments_list = None
    if attachments_blob is not None:
        try:
            # Use pickle.loads to convert the byte string back to the object list
            attachments_list = pickle.loads(attachments_blob)
        except pickle.UnpicklingError:
            # Handle case where the BLOB is corrupted or not a valid pickle stream
            print(
                f"Warning: Could not unpickle attachments for message {data['entryID']}"
            )
            attachments_list = None

    entry = logClasses.MessageLogEntry(
        customID=data["entryID"],
        customTimestamp=timestamp_obj,
        discordMessageID=data["discordMessageID"],
        messageTypes=message_types_list,
        guildName=data["guildName"],
        channelID=data["channelID"],
        channelName=data["channelName"],
        userID=data["userID"],
        userName=data["userName"],
        isBot=bool(
            data["isBot"]
        ),  # Ensure boolean is correctly parsed from DB int/bool type
        wordCount=data["wordCount"],
        # Optional fields
        guildID=data["guildID"],
        userNickname=data["userNickname"],
        content=data["content"],
        systemContent=data["systemContent"],
        attachments=attachments_list,
    )

    return entry
