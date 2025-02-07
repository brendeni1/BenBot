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
            result.append(f"{count}{unit}")
        # Stop once we have two nonzero units.
        if len(result) == 2:
            break

    # If all units are zero, return "0s".
    return " ".join(result) if result else "0s"