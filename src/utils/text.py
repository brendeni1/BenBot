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