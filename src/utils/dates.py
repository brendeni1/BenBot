import datetime
from dateutil import parser

def formatSeconds(seconds: int):
    """
    Convert an integer number of seconds into a string with at most two time units.
    
    Examples:
      format_duration(3025500)  --> "35d 25m"
      format_duration(3661)     --> "1h 1m"
      format_duration(59)       --> "59s"
    
    Parameters:
      seconds (int): The total seconds (must be non-negative).
      
    Returns:
      str: The formatted duration string.
    """
    if seconds < 0:
        raise ValueError("Seconds must be non-negative")
    
    # Define units in descending order along with their corresponding number of seconds.
    units = [
        ('d', 86400),  # 1 day = 86400 seconds
        ('h', 3600),   # 1 hour = 3600 seconds
        ('m', 60),     # 1 minute = 60 seconds
        ('s', 1)       # 1 second = 1 second
    ]
    
    result = []
    for unit, unit_seconds in units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            seconds %= unit_seconds
            result.append(f"{round(count)}{unit}")
        # Stop once we have two nonzero units.
        if len(result) == 2:
            break

    # If all units are zero, return "0s".
    return " ".join(result) if result else "0s"

def formatSimpleDate(timestamp: str | datetime.datetime = None, *, includeTime: bool = True, timeNow: bool = False) -> str:
    if not timestamp and not timeNow:
        raise ValueError("No timestamp provided to src.utils.dates.formatSimpleDate.")
    
    if timeNow:
        timestamp = datetime.datetime.now()
    
    if not isinstance(timestamp, datetime.datetime):
        timestamp = parser.parse(timestamp)

    if includeTime:
        formattedDate = timestamp.strftime("%b %#d %Y %#I:%M %p")
    else:
        formattedDate = timestamp.strftime("%b %-d %Y")
    
    return formattedDate

def simpleDateObj(timestamp: None | datetime.datetime | str = None, *, timeNow: bool = False) -> str:
    if not timestamp and not timeNow:
        raise ValueError("No timestamp provided to src.utils.dates.simpleDateObj.")
    
    if timeNow:
        timestamp = datetime.datetime.now()
    
    if not isinstance(timestamp, datetime.datetime):
        timestamp = timestamp = parser.parse(timestamp)

    return timestamp

def deltaInSeconds(timestamp1: str | datetime.datetime, timestamp2: str | datetime.datetime | None = None, *, againstTimeNow: bool = False, utc = False) -> int:
    if not timestamp2 and not againstTimeNow:
        raise ValueError("No 2 timestamps provided to src.utils.dates.deltaInSeconds or againstTimeNow not specified.")
    
    if againstTimeNow:
        if utc:
            timestamp2 = datetime.datetime.now(datetime.timezone.utc)
        else:
            timestamp2 = datetime.datetime.now()
    
    if not isinstance(timestamp1, datetime.datetime):
        if utc:
            timestamp1 = timestamp = parser.parse(timestamp1)

            timestamp1 = timestamp1.replace(tzinfo=datetime.timezone.utc)
        else:
            timestamp1 = timestamp = parser.parse(timestamp1)

    if not isinstance(timestamp2, datetime.datetime):
        if utc:
            timestamp2 = timestamp = parser.parse(timestamp2)

            timestamp2 = timestamp2.replace(tzinfo=datetime.timezone.utc)
        else:
            timestamp2 = timestamp = parser.parse(timestamp2)

    if utc:
        timestamp1 = timestamp1.replace(tzinfo=datetime.timezone.utc)
        timestamp2 = timestamp2.replace(tzinfo=datetime.timezone.utc)

    delta = timestamp1 - timestamp2
    
    return delta.total_seconds()