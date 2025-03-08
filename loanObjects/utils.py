from datetime import datetime
def check_is_valid_date(date : str):
    if not date:
        raise ValueError("date of birth is required.")
    if isinstance(date, str):
        try:
            return datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date of birth must be in YYYY-MM-DD format.")
    else:
        raise ValueError("date of birth must be provided as a string.")