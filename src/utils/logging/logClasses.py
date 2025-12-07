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
