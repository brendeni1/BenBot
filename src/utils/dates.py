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
        ("d", 86400),  # 1 day = 86400 seconds
        ("h", 3600),  # 1 hour = 3600 seconds
        ("m", 60),  # 1 minute = 60 seconds
        ("s", 1),  # 1 second = 1 second
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


def formatSimpleDate(
    timestamp: str | datetime.datetime | datetime.date = None,
    *,
    formatString: str = None,
    includeTime: bool = True,
    timeNow: bool = False,
    discordDateFormat: str = None,
    relativity: bool = True,
) -> str:
    """
    Format a date, datetime object, or string into a readable string or Discord's rich timestamp format.

    Parameters
    ----------
    timestamp : str | datetime.datetime | datetime.date, optional
        The date/time to format. Can be a datetime object, date object, or a
        string parsable by dateutil. If omitted, `timeNow` must be True.

    formatString : str, optional
        A custom strftime format string. If provided, this takes priority.
        Note: Using time directives (e.g., %H, %M) with a `date` object
        will raise a ValueError.

    includeTime : bool, default=True
        Whether to include the time component. Ignored if `formatString` or
        `discordDateFormat` is provided. Will be forced to False if
        the input `timestamp` is a `datetime.date` object.

    timeNow : bool, default=False
        If True, uses the current system time instead of requiring a `timestamp`.

    discordDateFormat : str, optional
        A Discord timestamp style code (e.g., "F", "R"). Takes precedence.

        Supported codes:
        - "t" → short time (e.g. 9:41 PM)
        - "T" → long time with seconds (e.g. 9:41:30 PM)
        - "d" → short date (e.g. 09/27/2025)
        - "D" → long date (e.g. September 27, 2025)
        - "f" → short date/time (e.g. September 27, 2025 9:41 PM)
        - "F" → long date/time (e.g. Saturday, September 27, 2025 9:41 PM)
        - "R" → relative time (e.g. "in 2 years", "3 days ago")

    relativity : bool, default=False
        If True, returns Yesterday/Today/Tomorrow for such dates instead of full date. Otherwise full date.

    Returns
    -------
    str
        A formatted string representation of the date.

    Raises
    ------
    ValueError
        If no timestamp is provided and `timeNow` is False.
    TypeError
        If the timestamp type is unsupported.
    """

    # --- 1. Resolve input to a date or datetime object ---
    obj: datetime.datetime | datetime.date

    if not timestamp and not timeNow:
        raise ValueError("No timestamp provided to formatSimpleDate.")

    if timeNow:
        obj = datetime.datetime.now()
    elif isinstance(timestamp, (datetime.datetime, datetime.date)):
        obj = timestamp
    elif isinstance(timestamp, str):
        obj = parser.parse(timestamp)
    else:
        raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")

    # Check if the resolved object has a time component.
    # datetime.datetime is a subclass of datetime.date, so we check
    # if it's an instance of the more specific datetime.datetime.
    has_time_component = isinstance(obj, datetime.datetime)

    # --- 2. Handle Discord Format (requires a datetime) ---
    if discordDateFormat:
        dt_for_discord: datetime.datetime
        if has_time_component:
            dt_for_discord = obj
        else:
            # Convert pure date to datetime at midnight
            dt_for_discord = datetime.datetime.combine(obj, datetime.time.min)

        unix_ts = int(dt_for_discord.timestamp())
        return f"<t:{unix_ts}:{discordDateFormat}>"

    # --- 3. Handle Custom Format String ---
    if formatString:
        # Let user be responsible for format string compatibility
        return obj.strftime(formatString)

    # --- 4. Handle Default Formatting (MODIFIED SECTION) ---

    date_part_str = ""
    time_part_str = ""

    # --- 4a. Resolve Date Part with Relativity ---
    if relativity:
        today = datetime.date.today()

        # Get just the date part of the input object
        input_date = obj.date() if has_time_component else obj

        delta_days = (input_date - today).days

        if delta_days == 0:
            date_part_str = "Today"
        elif delta_days == -1:
            date_part_str = "Yesterday"
        elif delta_days == 1:
            date_part_str = "Tomorrow"
        else:
            # Fallback for dates not Yesterday/Today/Tomorrow
            date_part_str = obj.strftime("%b %-d %Y")
    else:
        # Standard date formatting
        date_part_str = obj.strftime("%b %-d %Y")

    # --- 4b. Resolve Time Part ---
    # Include time only if requested AND available
    if includeTime and has_time_component:
        # Use strftime directives for 12-hour clock, minute, and AM/PM
        # (%#I on Windows, %-I on Linux/macOS to remove leading zero)
        # Using %#I as it was in your original.
        time_part_str = obj.strftime("%-I:%M %p")

    # --- 4c. Combine and Return ---
    if time_part_str:
        return f"{date_part_str} {time_part_str}"
    else:
        return date_part_str


def simpleDateObj(
    timestamp: None | datetime.datetime | datetime.date | str = None,
    *,
    timeNow: bool = False,
) -> datetime.datetime:
    """
    Ensures a datetime.datetime object is returned from various inputs.

    Parameters
    ----------
    timestamp : None | datetime.datetime | datetime.date | str, optional
        The input to convert. Can be a datetime, date, string, or None.
    timeNow : bool, default=False
        If True, uses the current system time instead of requiring a `timestamp`.

    Returns
    -------
    datetime.datetime
        A datetime object. If input was a `date`, time is set to midnight.

    Raises
    ------
    ValueError
        If no timestamp is provided and `timeNow` is False.
    TypeError
        If the timestamp type is unsupported.
    """
    if not timestamp and not timeNow:
        raise ValueError("No timestamp provided to simpleDateObj.")

    if timeNow:
        return datetime.datetime.now()

    if isinstance(timestamp, datetime.datetime):
        return timestamp

    if isinstance(timestamp, datetime.date):
        # Convert date to datetime at midnight (start of the day)
        return datetime.datetime.combine(timestamp, datetime.time.min)

    if isinstance(timestamp, str):
        return parser.parse(timestamp)

    raise TypeError(f"Unsupported timestamp type: {type(timestamp)}")


def deltaInSeconds(
    timestamp1: str | datetime.datetime,
    timestamp2: str | datetime.datetime | None = None,
    *,
    againstTimeNow: bool = False,
    utc=False,
) -> int:
    if not timestamp2 and not againstTimeNow:
        raise ValueError(
            "No 2 timestamps provided to src.utils.dates.deltaInSeconds or againstTimeNow not specified."
        )

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


def dateRange(
    start: datetime.datetime,
    end: datetime.datetime,
    step: datetime.timedelta = datetime.timedelta(days=1),
):
    current = start

    while current <= end:
        yield current
        current += step
