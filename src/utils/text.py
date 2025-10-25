from src import constants

def truncateString(string: str, maxLength: int, addElipsis: bool = True, splitOnMax = False) -> list[str]:
    if maxLength < 4 and addElipsis:
        raise ValueError("Cannot add an elipsis with a maxLength less than 4 chars.")
    
    if len(string) > maxLength:
        if splitOnMax:
            truncatedString = [string[i:i+maxLength] for i in range(0, len(string), maxLength)]
        else:
            truncatedString = [string[:maxLength - 3] + "..."]
    else:
        truncatedString = [string]
    
    return truncatedString

def numberToEmoji(number: int, emojiMap: dict[str] = constants.EMOJI_MAP, emojiIfSingleDigitsOnly: str | None = None) -> str:
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
