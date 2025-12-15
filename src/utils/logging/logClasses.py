import datetime
import pickle

from src.utils import text
from src.utils import dates

from src.classes import LocalDatabase


class LogEntry:
    def __init__(
        self,
        *,
        customID: str | None = None,
        customTimestamp: datetime.datetime | None = None,
    ):
        self.id = customID if customID is not None else text.generateUUID()
        self.timestamp = (
            customTimestamp
            if customTimestamp is not None
            else dates.simpleDateObj(timeNow=True)
        )


class CommandLogEntry(LogEntry):
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
        invocationOptions: str = None,
    ):
        super().__init__(customID=customID, customTimestamp=customTimestamp)

        self.qualifiedCommandName = qualifiedCommandName
        self.invocationGuildID = invocationGuildID
        self.invocationGuildName = invocationGuildName
        self.invocationChannelID = invocationChannelID
        self.invocationChannelName = invocationChannelName
        self.invocationUserID = invocationUserID
        self.invocationOptions = invocationOptions

    def optionsToDict(self) -> dict[str]:
        return dict(self.invocationOptions)


class SmallDiscordAttachment:
    def __init__(
        self,
        discordID: int,
        sizeBytes: int,
        fileName: str,
        link: str,
        description: str | None = None,
        mediaType: str | None = None,
        height: int | None = None,
        width: int | None = None,
    ):
        # Mandatory fields
        self.discordID: int = discordID
        self.sizeBytes: int = sizeBytes
        self.fileName: str = fileName
        self.link: str = link

        # Optional fields
        self.description: str | None = description
        self.mediaType: str | None = mediaType
        self.height: int | None = height
        self.width: int | None = width

    def serializeAttachment(self) -> bytes:
        serialized = pickle.dumps(self)

        return serialized


class MessageLogEntry(LogEntry):
    """
    Represents a single message log entry, mapping directly to the 'messages' SQL table schema.
    """

    def __init__(
        self,
        *,
        customID: str | None = None,
        customTimestamp: datetime.datetime | None = None,
        discordMessageID: int,
        messageTypes: list[str],
        guildName: str,
        channelID: int,
        channelName: str,
        userID: int,
        userName: str,
        isBot: bool,
        wordCount: int,
        guildID: int | None = None,
        userNickname: str | None = None,
        content: str | None = None,
        systemContent: str | None = None,
        attachments: list[SmallDiscordAttachment] | None = None,
    ):
        super().__init__(customID=customID, customTimestamp=customTimestamp)

        self.discordMessageID: int = discordMessageID
        self.messageTypes: list[str] = messageTypes

        self.guildID: int | None = guildID
        self.userNickname: str | None = userNickname
        self.systemContent: str | None = systemContent
        self.content: str | None = content
        self.attachments: list[SmallDiscordAttachment] | None = attachments

        self.guildName: str = guildName
        self.channelID: int = channelID
        self.channelName: str = channelName
        self.userID: int = userID
        self.userName: str = userName
        self.isBot: bool = isBot
        self.wordCount: int = wordCount

    def serializeAttachments(self) -> bytes | None:
        if not self.attachments:
            return None

        serialized = pickle.dumps(self.attachments)

        return serialized

    def writeToDB(self, db: str = "logs", table: str = "messages") -> None:
        database = LocalDatabase(database=db)

        sql = f"""
        INSERT INTO {table} (`entryID`, `discordMessageID` , `timestamp`, `messageTypes`, `guildID`, `guildName`, `channelID`, `channelName`, `userID`, `userName`, `userNickname`, `content`, `systemContent`, `attachments`, `isBot`, `wordCount`)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

        params = (
            self.id,
            self.discordMessageID,
            dates.formatSimpleDate(self.timestamp, databaseDate=True),
            str(self.messageTypes),
            self.guildID,
            self.guildName,
            self.channelID,
            self.channelName,
            self.userID,
            self.userName,
            self.userNickname,
            self.content,
            self.systemContent,
            self.serializeAttachments(),
            self.isBot,
            self.wordCount,
        )

        database.setOne(sql, params)
