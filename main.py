from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging

from models import FitnessClass, BookingRequest, BookingResponse, BookingHistory, ErrorResponse
from services import BookingService
from utils import log_error, get_current_ist_time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Fitness Studio Booking API",
    description="A simple booking API for a fictional fitness studio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "message": "Fitness Studio Booking API",
        "version": "1.0.0",
        "status": "running",
        "current_time_ist": get_current_ist_time().isoformat()
    }


@app.get("/classes", response_model=List[FitnessClass], tags=["Classes"])
async def get_classes():
    """
    Get all upcoming fitness classes.
    
    Returns a list of all available fitness classes with their details including
    name, date/time, instructor, and available slots.
    """
    try:
        classes = BookingService.get_all_classes()
        return classes
    except Exception as e:
        log_error("Error in get_classes endpoint", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/book", response_model=BookingResponse, tags=["Bookings"])
async def book_class(booking_request: BookingRequest):
    """
    Book a fitness class.
    
    Accepts a booking request with class_id, client_name, and client_email.
    Validates availability and creates the booking if slots are available.
    """
    try:
        # Validate the booking request
        is_valid, message = BookingService.validate_booking_request(booking_request)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Create the booking
        booking_response = BookingService.create_booking(booking_request)
        if not booking_response:
            raise HTTPException(status_code=400, detail="Failed to create booking. Please try again.")
        
        return booking_response
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("Error in book_class endpoint", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/bookings", response_model=List[BookingHistory], tags=["Bookings"])
async def get_bookings(email: str = Query(..., description="Email address to get bookings for")):
    """
    Get all bookings for a specific email address.
    
    Returns a list of all bookings made by the specified email address.
    """
    try:
        if not email or "@" not in email:
            raise HTTPException(status_code=400, detail="Valid email address is required")
        
        bookings = BookingService.get_bookings_by_email(email)
        return bookings
        
    except HTTPException:
        raise
    except Exception as e:
        log_error("Error in get_bookings endpoint", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/stats", tags=["Statistics"])
async def get_booking_statistics():
    """
    Get booking statistics.
    
    Returns overall statistics about classes and bookings.
    """
    try:
        stats = BookingService.get_booking_statistics()
        return {
            "statistics": stats,
            "current_time_ist": get_current_ist_time().isoformat()
        }
    except Exception as e:
        log_error("Error in get_booking_statistics endpoint", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/classes/{class_id}", response_model=FitnessClass, tags=["Classes"])
async def get_class_by_id(class_id: int):
    """
    Get a specific class by ID.
    
    Returns details of a specific fitness class.
    """
    try:
        if class_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid class ID")
        
        fitness_class = BookingService.get_class_by_id(class_id)
        if not fitness_class:
            raise HTTPException(status_code=404, detail="Class not found")
        
        return fitness_class
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(f"Error in get_class_by_id endpoint for class {class_id}", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Resource not found", "detail": "The requested resource was not found"}


@app.exception_handler(422)
async def validation_error_handler(request, exc):
    return {"error": "Validation error", "detail": "Invalid request data"}


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error", "detail": "An unexpected error occurred"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8671) 