from uuid import uuid4
from rapidfuzz import process

from src import constants


def generateUUID():
    return uuid4().hex


def truncateString(
    string: str, maxLength: int, addElipsis: bool = True, splitOnMax=False
) -> list[str]:
    if maxLength < 4 and addElipsis:
        raise ValueError("Cannot add an elipsis with a maxLength less than 4 chars.")

    if len(string) > maxLength:
        if splitOnMax:
            truncatedString = [
                string[i : i + maxLength] for i in range(0, len(string), maxLength)
            ]
        else:
            truncatedString = [string[: maxLength - 3] + "..."]
    else:
        truncatedString = [string]

    return truncatedString


def numberToEmoji(
    number: int,
    emojiMap: dict[str] = constants.EMOJI_MAP,
    emojiIfSingleDigitsOnly: str | None = None,
) -> str:
    finished = ""

    if len(str(number)) > 1 and emojiIfSingleDigitsOnly:
        return emojiIfSingleDigitsOnly

    for number in str(number):
        finished += emojiMap[number]

    return finished


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def smartRound(x, ndigits=1):
    rounded = round(x, ndigits)

    if rounded.is_integer():
        return int(rounded)

    return rounded


def frange(start, stop=None, step=1.0):
    """
    A float-friendly version of range().

    Examples:
        list(frange(0, 5, 0.5))  # [0.0, 0.5, 1.0, 1.5, ..., 4.5]
        list(frange(3))          # [0.0, 1.0, 2.0]
    """
    if stop is None:  # only one arg -> frange(stop)
        stop = start
        start = 0.0

    x = start
    if step > 0:
        while x < stop:
            yield round(x, 10)  # round avoids floating-point drift
            x += step
    elif step < 0:
        while x > stop:
            yield round(x, 10)
            x += step
    else:
        raise ValueError("frange() step argument must not be zero")


def ordinal(n: int) -> str:
    # Handle special cases like 11th, 12th, 13th
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def fuzzySearch(
    query: str, choices, limit: int | None = 1, scoreCutoff: float | None = None
) -> list[tuple]:
    results = process.extract(
        query=query, choices=choices, limit=limit, score_cutoff=scoreCutoff
    )

    return results


def truncateList(
    inputList: list[str], limit: int, addRestLength: bool = True
) -> list[str]:
    """
    Truncates a list of strings so that joining them with newlines stays within 'limit'.
    If truncation occurs and addRestLength is True, appends '... and X more...'.
    """
    currentLength = 0
    truncatedResult = []

    # 1 is the length of the newline character "\n" used for joining later
    separatorLength = 1

    for i, item in enumerate(inputList):
        # Calculate cost of adding this item (add separator cost only if not the first item)
        itemCost = len(item) + (separatorLength if i > 0 else 0)

        # Check if adding this item exceeds the limit
        if currentLength + itemCost > limit:
            remainingCount = len(inputList) - i

            if addRestLength:
                suffix = f"... and {remainingCount} more..."
                suffixCost = len(suffix) + separatorLength

                # If adding the suffix exceeds limit, remove previous items until it fits
                while truncatedResult and (currentLength + suffixCost > limit):
                    removedItem = truncatedResult.pop()
                    # Determine cost of the removed item (was it the first?)
                    removedCost = len(removedItem) + (
                        separatorLength if truncatedResult else 0
                    )
                    currentLength -= removedCost
                    remainingCount += 1

                    # Update suffix with new count
                    suffix = f"... and {remainingCount} more..."
                    suffixCost = len(suffix) + separatorLength

                truncatedResult.append(suffix)

            return truncatedResult

        truncatedResult.append(item)
        currentLength += itemCost

    return truncatedResult


def formatBytes(amount: int) -> str:
    """
    Translates bytes to the most suitable unit (KB, MB, GB, etc.).
    Uses the binary (base 1024) system.
    """
    if amount == 0:
        return "0 Bytes"

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB"]
    unit = 1024
    i = 0

    # Find the correct unit exponent
    while amount >= unit and i < len(units) - 1:
        amount /= unit
        i += 1

    return f"{amount:.1f} {units[i]}"
