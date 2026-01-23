import datetime

from src.classes import *

from src.utils.logging import commandLogs, logClasses


def tallyByEntryAttribute(
    entries: list[logClasses.CommandLogEntry], key: str, reverseSort: bool = False
) -> list[tuple[str, int]]:
    counted = {}

    for entry in entries:
        name = str(getattr(entry, key))
        counted[name] = counted.get(name, 0) + 1

    # Return a sorted list, not a dict
    sorted_counts = sorted(counted.items(), key=lambda x: x[1], reverse=reverseSort)

    return sorted_counts


def fetchCommandLogs(
    *,
    filterLogIDS: list[str] = None,
    filterLogStartDate: datetime.datetime = None,
    filterLogEndDate: datetime.datetime = None,
    filterUsers: list[int] = None,
    filterGuilds: list[int] = None,
    filterChannels: list[int] = None,
    filterCommands: list[str] = None,
    includeDMS: bool = True,
    onlyDMS: bool = False
) -> list[logClasses.CommandLogEntry]:
    database = LocalDatabase(database="logs")

    sql = "SELECT * FROM commands ORDER BY timestamp DESC"

    rawLogEntries = database.get(sql)

    logEntryObjs = [
        commandLogs.dbResultToLogEntry(rawEntry) for rawEntry in rawLogEntries
    ]

    if not any(
        [
            filterLogIDS,
            filterLogStartDate,
            filterLogEndDate,
            filterUsers,
            filterGuilds,
            filterChannels,
            filterCommands,
            not includeDMS,
            onlyDMS,
        ]
    ):
        return logEntryObjs

    filteredLogEntries = []

    for entry in logEntryObjs:
        checks = []

        if entry.invocationGuildName == "DM" and (not includeDMS or not onlyDMS):
            continue

        if filterLogIDS:
            checks.append(entry.id in filterLogIDS)

        if filterLogStartDate:
            checks.append(entry.timestamp > filterLogStartDate)

        if filterLogEndDate:
            checks.append(entry.timestamp < filterLogEndDate)

        if filterUsers:
            checks.append(entry.invocationUserID in filterUsers)

        if filterGuilds:
            checks.append(entry.invocationGuildID in filterGuilds)

        if filterChannels:
            checks.append(entry.invocationChannelID in filterChannels)

        if filterCommands:
            checks.append(entry.qualifiedCommandName in filterCommands)

        if all(checks):
            filteredLogEntries.append(entry)

    return filteredLogEntries
