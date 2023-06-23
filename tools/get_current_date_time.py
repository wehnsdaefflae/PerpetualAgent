from datetime import datetime

def get_current_date_time() -> str:
    """
    Retrieve the current date and time.

    Example:
    >>> print(get_current_date_time())

    Returns:
    str: The string containing the current date and time.
    """
    # The datetime.now() function from the datetime module gets the current date and time.
    current_datetime = datetime.now()

    # Formatting the date time to a more readable string format.
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_datetime