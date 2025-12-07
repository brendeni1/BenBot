import datetime

from src.utils import text
from src.utils import dates


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
