import re

def multiRegexMatch(patterns: list[str], string: str, flags, allMustMatch: bool=False) -> bool:
    if allMustMatch:
        return all(re.match(regex, string, flags) for regex in patterns)
    
    return any(re.match(regex, string, flags) for regex in patterns)