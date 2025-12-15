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


def messageToLogEntryObj(message: discord.Message) -> logClasses.MessageLogEntry:
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
