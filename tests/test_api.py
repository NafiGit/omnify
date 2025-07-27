import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json

from main import app
from database import Database
from models import BookingRequest

client = TestClient(app)


class TestAPI:
    """Test cases for API endpoints"""
    
    def setup_method(self):
        """Setup test database"""
        # Reset database for each test
        self.db = Database(":memory:")
    
    def test_root_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Fitness Studio Booking API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "current_time_ist" in data
    
    def test_get_classes(self):
        """Test getting all classes"""
        response = client.get("/classes")
        assert response.status_code == 200
        classes = response.json()
        assert isinstance(classes, list)
        
        if classes:  # If there are classes
            class_data = classes[0]
            assert "id" in class_data
            assert "name" in class_data
            assert "date_time" in class_data
            assert "instructor" in class_data
            assert "available_slots" in class_data
            assert "total_slots" in class_data
    
    def test_get_class_by_id_valid(self):
        """Test getting a specific class by valid ID"""
        # First get all classes to get a valid ID
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            response = client.get(f"/classes/{class_id}")
            assert response.status_code == 200
            class_data = response.json()
            assert class_data["id"] == class_id
    
    def test_get_class_by_id_invalid(self):
        """Test getting a class with invalid ID"""
        response = client.get("/classes/999")
        assert response.status_code == 404
        assert "Class not found" in response.json()["detail"]
    
    def test_get_class_by_id_negative(self):
        """Test getting a class with negative ID"""
        response = client.get("/classes/-1")
        assert response.status_code == 400
        assert "Invalid class ID" in response.json()["detail"]
    
    def test_book_class_valid(self):
        """Test booking a class with valid data"""
        # First get a class to book
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            booking_data = {
                "class_id": class_id,
                "client_name": "John Doe",
                "client_email": "john@example.com"
            }
            
            response = client.post("/book", json=booking_data)
            assert response.status_code == 200
            booking_response = response.json()
            assert booking_response["class_name"] == classes[0]["name"]
            assert booking_response["client_name"] == "John Doe"
            assert booking_response["client_email"] == "john@example.com"
            assert "Booking successful!" in booking_response["message"]
    
    def test_book_class_invalid_class_id(self):
        """Test booking with invalid class ID"""
        booking_data = {
            "class_id": 999,
            "client_name": "John Doe",
            "client_email": "john@example.com"
        }
        
        response = client.post("/book", json=booking_data)
        assert response.status_code == 400
        assert "Class not found" in response.json()["detail"]
    
    def test_book_class_invalid_email(self):
        """Test booking with invalid email"""
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            booking_data = {
                "class_id": class_id,
                "client_name": "John Doe",
                "client_email": "invalid-email"
            }
            
            response = client.post("/book", json=booking_data)
            assert response.status_code == 422  # Validation error
    
    def test_book_class_empty_name(self):
        """Test booking with empty client name"""
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            booking_data = {
                "class_id": class_id,
                "client_name": "",
                "client_email": "john@example.com"
            }
            
            response = client.post("/book", json=booking_data)
            assert response.status_code == 422  # Validation error
    
    def test_book_class_duplicate(self):
        """Test booking the same class twice with same email"""
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            booking_data = {
                "class_id": class_id,
                "client_name": "John Doe",
                "client_email": "john@example.com"
            }
            
            # First booking should succeed
            response = client.post("/book", json=booking_data)
            assert response.status_code == 200
            
            # Second booking should fail
            response = client.post("/book", json=booking_data)
            assert response.status_code == 400
            assert "already booked" in response.json()["detail"]
    
    def test_get_bookings_valid_email(self):
        """Test getting bookings for valid email"""
        # First make a booking
        response = client.get("/classes")
        classes = response.json()
        
        if classes:
            class_id = classes[0]["id"]
            booking_data = {
                "class_id": class_id,
                "client_name": "John Doe",
                "client_email": "john@example.com"
            }
            
            client.post("/book", json=booking_data)
            
            # Now get bookings for this email
            response = client.get("/bookings?email=john@example.com")
            assert response.status_code == 200
            bookings = response.json()
            assert isinstance(bookings, list)
            
            if bookings:
                booking = bookings[0]
                assert booking["client_email"] == "john@example.com"
                assert booking["client_name"] == "John Doe"
    
    def test_get_bookings_invalid_email(self):
        """Test getting bookings with invalid email"""
        response = client.get("/bookings?email=invalid-email")
        assert response.status_code == 400
        assert "Valid email address is required" in response.json()["detail"]
    
    def test_get_bookings_missing_email(self):
        """Test getting bookings without email parameter"""
        response = client.get("/bookings")
        assert response.status_code == 422  # Validation error
    
    def test_get_booking_statistics(self):
        """Test getting booking statistics"""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        assert "current_time_ist" in data
        
        stats = data["statistics"]
        assert "total_classes" in stats
        assert "total_slots" in stats
        assert "available_slots" in stats
        assert "booked_slots" in stats
        assert "booking_percentage" in stats
    
    def test_booking_validation_model(self):
        """Test Pydantic model validation"""
        # Test valid booking request
        valid_booking = BookingRequest(
            class_id=1,
            client_name="John Doe",
            client_email="john@example.com"
        )
        assert valid_booking.class_id == 1
        assert valid_booking.client_name == "John Doe"
        assert valid_booking.client_email == "john@example.com"
        
        # Test email normalization
        booking_with_uppercase_email = BookingRequest(
            class_id=1,
            client_name="John Doe",
            client_email="JOHN@EXAMPLE.COM"
        )
        assert booking_with_uppercase_email.client_email == "john@example.com"
    
    def test_error_handlers(self):
        """Test error handlers"""
        # Test 404 error
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test 422 error (validation error)
        response = client.post("/book", json={"invalid": "data"})
        assert response.status_code == 422 