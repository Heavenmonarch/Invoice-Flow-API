from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def current_period() -> str:
    """
    Returns current month as period string  
    """
    return utc_now().strftime("%Y-%m")

def format_period(dt: datetime) -> str:
    """Convert any datetime to a period string"""
    return dt.strftime("%Y-%m")


def parse_period(period: str) -> tuple[int, int]:
    # parse a period string into (year. month)
    
    try:
        dt = datetime.strptime(period, "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        raise ValueError(f"Invalid period format '{period}'. Expected YYYY-MM")
    
def period_range(start: str, end: str) -> list[str]:
    # Returns all period strings between two periods inclusive
    # eg period_range('2025-01', '2025-03') -> ['2025-01', '2025-02']
    
    start_year, start_month = parse_period(start)
    end_year, end_month = parse_period(end)
    
    periods = []
    year, month = start_year, start_month
    
    while (year, month) <= (end_year, end_month):
        periods.append(f"{year:04d}-{month:02d}")
        month +=1
        if month > 12:
            month = 1
            year += 1