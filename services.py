from datetime import datetime
from typing import List, Optional, Dict, Any
from database import get_db
from models import FitnessClass, BookingRequest, BookingResponse, BookingHistory
from utils import (
    convert_to_ist, 
    is_future_class, 
    log_booking_activity, 
    log_error,
    get_current_ist_time
)


class BookingService:
    """Service layer for booking operations"""
    
    @staticmethod
    def get_all_classes() -> List[FitnessClass]:
        """Get all upcoming fitness classes"""
        try:
            db = get_db()
            classes_data = db.get_all_classes()
            classes = []
            
            for class_data in classes_data:
                # Convert string datetime to datetime object
                date_time = datetime.fromisoformat(class_data['date_time'])
                
                # Only include future classes
                if is_future_class(date_time):
                    classes.append(FitnessClass(
                        id=class_data['id'],
                        name=class_data['name'],
                        date_time=date_time,
                        instructor=class_data['instructor'],
                        available_slots=class_data['available_slots'],
                        total_slots=class_data['total_slots']
                    ))
            
            return classes
            
        except Exception as e:
            log_error("Error getting all classes", str(e))
            return []
    
    @staticmethod
    def get_class_by_id(class_id: int) -> Optional[FitnessClass]:
        """Get a specific class by ID"""
        try:
            db = get_db()
            class_data = db.get_class_by_id(class_id)
            if not class_data:
                return None
            
            date_time = datetime.fromisoformat(class_data['date_time'])
            
            # Check if class is in the future
            if not is_future_class(date_time):
                return None
            
            return FitnessClass(
                id=class_data['id'],
                name=class_data['name'],
                date_time=date_time,
                instructor=class_data['instructor'],
                available_slots=class_data['available_slots'],
                total_slots=class_data['total_slots']
            )
            
        except Exception as e:
            log_error(f"Error getting class {class_id}", str(e))
            return None
    
    @staticmethod
    def create_booking(booking_request: BookingRequest) -> Optional[BookingResponse]:
        """Create a new booking"""
        try:
            # Validate class exists and is in the future
            fitness_class = BookingService.get_class_by_id(booking_request.class_id)
            if not fitness_class:
                log_error("Booking failed", f"Class {booking_request.class_id} not found or not available")
                return None
            
            # Check if slots are available
            if fitness_class.available_slots <= 0:
                log_error("Booking failed", f"No available slots for class {booking_request.class_id}")
                return None
            
            # Create booking in database
            db = get_db()
            booking_id = db.create_booking(
                booking_request.class_id,
                booking_request.client_name,
                booking_request.client_email
            )
            
            if not booking_id:
                log_error("Booking failed", "Database error or duplicate booking")
                return None
            
            # Log successful booking
            log_booking_activity(
                booking_request.client_email,
                fitness_class.name,
                "created"
            )
            
            return BookingResponse(
                booking_id=booking_id,
                class_name=fitness_class.name,
                client_name=booking_request.client_name,
                client_email=booking_request.client_email,
                booking_date=fitness_class.date_time,
                message="Booking successful!"
            )
            
        except Exception as e:
            log_error("Error creating booking", str(e))
            return None
    
    @staticmethod
    def get_bookings_by_email(email: str) -> List[BookingHistory]:
        """Get all bookings for a specific email"""
        try:
            db = get_db()
            bookings_data = db.get_bookings_by_email(email)
            bookings = []
            
            for booking_data in bookings_data:
                date_time = datetime.fromisoformat(booking_data['booking_date'])
                
                bookings.append(BookingHistory(
                    id=booking_data['id'],
                    class_name=booking_data['class_name'],
                    client_name=booking_data['client_name'],
                    client_email=booking_data['client_email'],
                    booking_date=date_time
                ))
            
            return bookings
            
        except Exception as e:
            log_error(f"Error getting bookings for {email}", str(e))
            return []
    
    @staticmethod
    def validate_booking_request(booking_request: BookingRequest) -> tuple[bool, str]:
        """Validate booking request"""
        try:
            # Check if class exists
            fitness_class = BookingService.get_class_by_id(booking_request.class_id)
            if not fitness_class:
                return False, "Class not found or not available"
            
            # Check if slots are available
            if fitness_class.available_slots <= 0:
                return False, "No available slots for this class"
            
            # Check if client already booked this class
            existing_bookings = BookingService.get_bookings_by_email(booking_request.client_email)
            for booking in existing_bookings:
                if booking.class_name == fitness_class.name and booking.booking_date == fitness_class.date_time:
                    return False, "You have already booked this class"
            
            return True, "Valid booking request"
            
        except Exception as e:
            log_error("Error validating booking request", str(e))
            return False, "Validation error occurred"
    
    @staticmethod
    def get_booking_statistics() -> Dict[str, Any]:
        """Get booking statistics"""
        try:
            all_classes = BookingService.get_all_classes()
            total_classes = len(all_classes)
            total_slots = sum(c.total_slots for c in all_classes)
            available_slots = sum(c.available_slots for c in all_classes)
            booked_slots = total_slots - available_slots
            
            return {
                "total_classes": total_classes,
                "total_slots": total_slots,
                "available_slots": available_slots,
                "booked_slots": booked_slots,
                "booking_percentage": round((booked_slots / total_slots * 100), 2) if total_slots > 0 else 0
            }
            
        except Exception as e:
            log_error("Error getting booking statistics", str(e))
            return {} 