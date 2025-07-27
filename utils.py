import pytz
from datetime import datetime, timedelta
import logging
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# IST timezone
IST = pytz.timezone('Asia/Kolkata')


def get_current_ist_time() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)


def convert_to_ist(dt: datetime) -> datetime:
    """Convert datetime to IST timezone"""
    if dt.tzinfo is None:
        # If naive datetime, assume it's in IST
        return IST.localize(dt)
    return dt.astimezone(IST)


def is_future_class(class_datetime: datetime) -> bool:
    """Check if class is in the future"""
    current_time = get_current_ist_time()
    return convert_to_ist(class_datetime) > current_time


def format_datetime_for_display(dt: datetime) -> str:
    """Format datetime for display"""
    ist_dt = convert_to_ist(dt)
    return ist_dt.strftime("%Y-%m-%d %H:%M IST")


def validate_class_datetime(date_time: datetime) -> bool:
    """Validate if class datetime is valid (not in past)"""
    if not is_future_class(date_time):
        logger.warning(f"Attempted to create class in the past: {date_time}")
        return False
    return True


def get_upcoming_classes_filter():
    """Get filter for upcoming classes only"""
    current_time = get_current_ist_time()
    return lambda class_dt: convert_to_ist(class_dt) > current_time


def log_booking_activity(client_email: str, class_name: str, action: str):
    """Log booking activities"""
    logger.info(f"Booking {action}: {client_email} - {class_name}")


def log_error(error: str, detail: Optional[str] = None):
    """Log errors"""
    if detail:
        logger.error(f"{error}: {detail}")
    else:
        logger.error(error) 