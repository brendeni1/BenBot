def formatSeconds(seconds):
    # Define the time units in seconds
    minute = 60
    hour = 60 * minute
    day = 24 * hour

    # Calculate the breakdown
    days = seconds // day
    seconds %= day

    hours = seconds // hour
    seconds %= hour

    minutes = seconds // minute
    seconds %= minute

    # Create a dictionary to hold the time units
    time_units = {
        'd': days,
        'h': hours,
        'm': minutes,
        's': seconds
    }

    # Filter out units with zero value
    non_zero_units = {k: v for k, v in time_units.items() if v > 0}

    # Sort by value in descending order
    sorted_units = sorted(non_zero_units.items(), key=lambda x: x[1], reverse=True)

    # Only take the top 2 units
    top_units = sorted_units[:2]

    # Format the output
    if len(top_units) == 0:
        return "0 seconds"
    elif len(top_units) == 1:
        return f"{top_units[0][1]}{top_units[0][0]}"
    else:
        return f"{top_units[1][1]}{top_units[1][0]} {top_units[0][1]}{top_units[0][0]}"