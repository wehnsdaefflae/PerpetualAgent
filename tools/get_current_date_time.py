# coding=utf-8
from datetime import datetime


def get_current_date_time() -> str:
    """
    Retrieves the current date and time, expressed as a string in the format "YYYY-MM-DD HH:MM:SS".

    This function can be used in any scenario where current time stamping is required, such as logging events,
    creating time-based unique identifiers, or recording the execution time of tasks.

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
