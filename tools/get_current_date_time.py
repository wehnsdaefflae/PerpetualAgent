# coding=utf-8
from datetime import datetime


def get_current_date_time() -> str:
    """Retrieves the current date and time as a string in the standard "YYYY-MM-DD HH:MM:SS" format.

    This function fetches the current date and time and formats it as a string in the international standard date and time notation "YYYY-MM-DD HH:MM:SS". It can be implemented in a variety of situations where time stamping is needed such as event logging, creation of time-based unique identifiers, or tracking the execution duration of certain tasks.

    Example:
        >>> get_current_date_time()

    Args:
        None

    Returns:
        str: A string representation of the current date and time in "YYYY-MM-DD HH:MM:SS" format.
    """
    # The datetime.now() function from the datetime module gets the current date and time.
    current_datetime = datetime.now()

    # Formatting the date time to a more readable string format.
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_datetime
