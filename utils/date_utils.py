import datetime
from datetime import timedelta
import calendar

def get_last_month_range():
    """
    Returns the start and end date of the previous month.
    """
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_day_last_month = first_day_this_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    return first_day_last_month, last_day_last_month

def parse_relative_date(date_str, relative_to=None):
    """
    Parses a date string from YouTube history which can be:
    - "Today"
    - "Yesterday"
    - A day of the week (e.g., "Wednesday") - implies the most recent past occurrence
    - An absolute date (e.g., "Jan 31", "Feb 28, 2024")
    
    Args:
        date_str (str): The date string to parse.
        relative_to (datetime.date, optional): The reference date (defaults to today).
        
    Returns:
        datetime.date: The parsed date object.
    """
    if relative_to is None:
        relative_to = datetime.date.today()
        
    date_str = date_str.strip()
    
    # helper for cleaner comparisons
    lower_str = date_str.lower()
    
    if lower_str == "today":
        return relative_to
    
    if lower_str == "yesterday":
        return relative_to - timedelta(days=1)
        
    # Check for Day of Week (Monday, Tuesday, etc.)
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    if lower_str in days_of_week:
        target_weekday = days_of_week.index(lower_str)
        current_weekday = relative_to.weekday()
        
        # Calculate days to subtract to get to the target weekday
        # If today is Wednesday (2) and we want Monday (0): 2 - 0 = 2 days ago
        # If today is Monday (0) and we want Wednesday (2): (0 - 2) % 7 = (-2) % 7 = 5 days ago
        days_ago = (current_weekday - target_weekday) % 7
        if days_ago == 0:
            days_ago = 7 # If it's the same day, YouTube likely means last week's occurrence? 
                         # Actually usually "Wednesday" on a Wednesday implies today, but YouTube says "Today"
                         # Let's assume strict past interpretation if ambiguous, but usually it won't be today.
        
        return relative_to - timedelta(days=days_ago)

    # Try parsing absolute formats
    # YouTube formats often depend on locale, but standard US/En is "Mon DD, YYYY" or just "Mon DD" (for current year)
    # Examples: "Jan 1, 2024", "Dec 31"
    
    # clean extra whitespace
    parts = date_str.split()
    
    # Basic check for Month Day (Year optional)
    # e.g. "Jan 31" or "Jan 31, 2024"
    if len(parts) >= 2:
        try:
            # Try with year
            return datetime.datetime.strptime(date_str, "%b %d, %Y").date()
        except ValueError:
            pass
            
        try:
            # Try without year (implies current year, or maybe previous year if month is ahead of current? 
            # YouTube usually adds year if it's not current year, let's assume current year for now)
            parsed_date = datetime.datetime.strptime(date_str, "%b %d").date()
            parsed_date = parsed_date.replace(year=relative_to.year)
            if parsed_date > relative_to:
                parsed_date = parsed_date.replace(year=relative_to.year - 1)
            return parsed_date
        except ValueError:
            pass

    # If we are here, we might need more formats or it's an error
    print(f"Warning: Could not parse date '{date_str}'")
    return None

if __name__ == "__main__":
    # verification/test block
    print("Testing get_last_month_range:")
    start, end = get_last_month_range()
    print(f"Last Month Start: {start}, End: {end}")
    
    print("\nTesting parse_relative_date:")
    test_dates = ["Today", "Yesterday", "Wednesday", "Jan 1, 2024", "Dec 25"]
    for d in test_dates:
        print(f"'{d}' -> {parse_relative_date(d)}")

