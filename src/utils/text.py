def truncateString(string: str, maxLength: int, addElipsis: bool = True) -> str:
    if maxLength < 4 and not addElipsis:
        raise ValueError("Cannot add an elipsis with a maxLength less than 4.")
    
    if len(string) > maxLength:
        truncatedString = string[:maxLength - 3] + "..."

        return truncatedString
    
    return string