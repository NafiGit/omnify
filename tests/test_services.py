import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services import BookingService
from models import BookingRequest, FitnessClass
from database import Database
from utils import get_current_ist_time


class TestBookingService:
    """Test cases for BookingService"""
    
    def setup_method(self):
        """Setup test database"""
        self.db = Database(":memory:")
    
    def test_get_all_classes(self):
        """Test getting all classes"""
        classes = BookingService.get_all_classes()
        assert isinstance(classes, list)
        
        # All classes should be in the future
        current_time = get_current_ist_time()
        for fitness_class in classes:
            assert fitness_class.date_time > current_time
            assert isinstance(fitness_class, FitnessClass)
            assert fitness_class.id > 0
            assert fitness_class.name
            assert fitness_class.instructor
            assert fitness_class.available_slots >= 0
            assert fitness_class.total_slots > 0
    
    def test_get_class_by_id_valid(self):
        """Test getting class by valid ID"""
        # First get all classes to get a valid ID
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            fitness_class = BookingService.get_class_by_id(class_id)
            assert fitness_class is not None
            assert fitness_class.id == class_id
            assert isinstance(fitness_class, FitnessClass)
    
    def test_get_class_by_id_invalid(self):
        """Test getting class by invalid ID"""
        fitness_class = BookingService.get_class_by_id(999)
        assert fitness_class is None
    
    def test_create_booking_valid(self):
        """Test creating a valid booking"""
        # Get a class to book
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            original_slots = all_classes[0].available_slots
            
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="John Doe",
                client_email="john@example.com"
            )
            
            booking_response = BookingService.create_booking(booking_request)
            assert booking_response is not None
            assert booking_response.booking_id > 0
            assert booking_response.class_name == all_classes[0].name
            assert booking_response.client_name == "John Doe"
            assert booking_response.client_email == "john@example.com"
            assert "Booking successful!" in booking_response.message
            
            # Check that available slots decreased
            updated_class = BookingService.get_class_by_id(class_id)
            assert updated_class.available_slots == original_slots - 1
    
    def test_create_booking_invalid_class(self):
        """Test creating booking for invalid class"""
        booking_request = BookingRequest(
            class_id=999,
            client_name="John Doe",
            client_email="john@example.com"
        )
        
        booking_response = BookingService.create_booking(booking_request)
        assert booking_response is None
    
    def test_create_booking_no_slots(self):
        """Test creating booking when no slots available"""
        # Get a class and book all available slots
        all_classes = BookingService.get_all_classes()
        if all_classes and all_classes[0].available_slots > 0:
            class_id = all_classes[0].id
            available_slots = all_classes[0].available_slots
            
            # Book all available slots
            for i in range(available_slots):
                booking_request = BookingRequest(
                    class_id=class_id,
                    client_name=f"User {i}",
                    client_email=f"user{i}@example.com"
                )
                BookingService.create_booking(booking_request)
            
            # Try to book one more
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="Extra User",
                client_email="extra@example.com"
            )
            
            booking_response = BookingService.create_booking(booking_request)
            assert booking_response is None
    
    def test_create_booking_duplicate(self):
        """Test creating duplicate booking"""
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="John Doe",
                client_email="john@example.com"
            )
            
            # First booking should succeed
            booking_response1 = BookingService.create_booking(booking_request)
            assert booking_response1 is not None
            
            # Second booking should fail
            booking_response2 = BookingService.create_booking(booking_request)
            assert booking_response2 is None
    
    def test_get_bookings_by_email(self):
        """Test getting bookings by email"""
        # First create a booking
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="John Doe",
                client_email="john@example.com"
            )
            BookingService.create_booking(booking_request)
            
            # Get bookings for this email
            bookings = BookingService.get_bookings_by_email("john@example.com")
            assert isinstance(bookings, list)
            assert len(bookings) > 0
            
            booking = bookings[0]
            assert booking.client_email == "john@example.com"
            assert booking.client_name == "John Doe"
            assert booking.class_name == all_classes[0].name
    
    def test_get_bookings_by_email_no_bookings(self):
        """Test getting bookings for email with no bookings"""
        bookings = BookingService.get_bookings_by_email("nonexistent@example.com")
        assert isinstance(bookings, list)
        assert len(bookings) == 0
    
    def test_validate_booking_request_valid(self):
        """Test validating valid booking request"""
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="John Doe",
                client_email="john@example.com"
            )
            
            is_valid, message = BookingService.validate_booking_request(booking_request)
            assert is_valid is True
            assert "Valid booking request" in message
    
    def test_validate_booking_request_invalid_class(self):
        """Test validating booking request with invalid class"""
        booking_request = BookingRequest(
            class_id=999,
            client_name="John Doe",
            client_email="john@example.com"
        )
        
        is_valid, message = BookingService.validate_booking_request(booking_request)
        assert is_valid is False
        assert "Class not found" in message
    
    def test_validate_booking_request_no_slots(self):
        """Test validating booking request when no slots available"""
        all_classes = BookingService.get_all_classes()
        if all_classes and all_classes[0].available_slots > 0:
            class_id = all_classes[0].id
            available_slots = all_classes[0].available_slots
            
            # Book all available slots
            for i in range(available_slots):
                booking_request = BookingRequest(
                    class_id=class_id,
                    client_name=f"User {i}",
                    client_email=f"user{i}@example.com"
                )
                BookingService.create_booking(booking_request)
            
            # Try to validate booking for full class
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="Extra User",
                client_email="extra@example.com"
            )
            
            is_valid, message = BookingService.validate_booking_request(booking_request)
            assert is_valid is False
            assert "No available slots" in message
    
    def test_validate_booking_request_duplicate(self):
        """Test validating duplicate booking request"""
        all_classes = BookingService.get_all_classes()
        if all_classes:
            class_id = all_classes[0].id
            
            booking_request = BookingRequest(
                class_id=class_id,
                client_name="John Doe",
                client_email="john@example.com"
            )
            
            # Create first booking
            BookingService.create_booking(booking_request)
            
            # Try to validate duplicate booking
            is_valid, message = BookingService.validate_booking_request(booking_request)
            assert is_valid is False
            assert "already booked" in message
    
    def test_get_booking_statistics(self):
        """Test getting booking statistics"""
        stats = BookingService.get_booking_statistics()
        assert isinstance(stats, dict)
        assert "total_classes" in stats
        assert "total_slots" in stats
        assert "available_slots" in stats
        assert "booked_slots" in stats
        assert "booking_percentage" in stats
        
        assert stats["total_classes"] >= 0
        assert stats["total_slots"] >= 0
        assert stats["available_slots"] >= 0
        assert stats["booked_slots"] >= 0
        assert 0 <= stats["booking_percentage"] <= 100
        
        # Verify calculations
        if stats["total_slots"] > 0:
            expected_percentage = round((stats["booked_slots"] / stats["total_slots"]) * 100, 2)
            assert stats["booking_percentage"] == expected_percentage
    
    def test_model_validation(self):
        """Test Pydantic model validation"""
        # Test valid booking request
        booking_request = BookingRequest(
            class_id=1,
            client_name="John Doe",
            client_email="john@example.com"
        )
        assert booking_request.class_id == 1
        assert booking_request.client_name == "John Doe"
        assert booking_request.client_email == "john@example.com"
        
        # Test email normalization
        booking_request = BookingRequest(
            class_id=1,
            client_name="John Doe",
            client_email="JOHN@EXAMPLE.COM"
        )
        assert booking_request.client_email == "john@example.com"
        
        # Test name trimming
        booking_request = BookingRequest(
            class_id=1,
            client_name="  John Doe  ",
            client_email="john@example.com"
        )
        assert booking_request.client_name == "John Doe"
    
    def test_fitness_class_model(self):
        """Test FitnessClass model"""
        current_time = get_current_ist_time()
        fitness_class = FitnessClass(
            id=1,
            name="Yoga",
            date_time=current_time + timedelta(days=1),
            instructor="Sarah Johnson",
            available_slots=10,
            total_slots=20
        )
        
        assert fitness_class.id == 1
        assert fitness_class.name == "Yoga"
        assert fitness_class.instructor == "Sarah Johnson"
        assert fitness_class.available_slots == 10
        assert fitness_class.total_slots == 20 