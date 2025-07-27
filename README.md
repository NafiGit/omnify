# Fitness Studio Booking API

A simple booking API for a fictional fitness studio built with FastAPI and SQLite.

## Features

- View all upcoming fitness classes
- Book classes with validation
- View bookings by email
- Timezone management (IST)
- Input validation and error handling
- Unit tests

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8671
   ```

3. **Access the API documentation:**
   - Swagger UI: http://localhost:8671/docs
   - ReDoc: http://localhost:8671/redoc

## API Endpoints

### 1. GET /classes
Returns a list of all upcoming fitness classes.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Yoga",
    "date_time": "2024-01-15T10:00:00+05:30",
    "instructor": "Sarah Johnson",
    "available_slots": 15,
    "total_slots": 20
  }
]
```

### 2. POST /book
Book a class for a client.

**Request Body:**
```json
{
  "class_id": 1,
  "client_name": "John Doe",
  "client_email": "john@example.com"
}
```

**Response:**
```json
{
  "booking_id": 1,
  "class_name": "Yoga",
  "client_name": "John Doe",
  "client_email": "john@example.com",
  "booking_date": "2024-01-15T10:00:00+05:30",
  "message": "Booking successful!"
}
```

### 3. GET /bookings?email=client@example.com
Returns all bookings for a specific email address.

**Response:**
```json
[
  {
    "id": 1,
    "class_name": "Yoga",
    "client_name": "John Doe",
    "client_email": "john@example.com",
    "booking_date": "2024-01-15T10:00:00+05:30"
  }
]
```

## Sample cURL Requests

### Get all classes
```bash
curl -X GET "http://localhost:8671/classes"
```

### Book a class
```bash
curl -X POST "http://localhost:8671/book" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": 1,
    "client_name": "John Doe",
    "client_email": "john@example.com"
  }'
```

### Get bookings by email
```bash
curl -X GET "http://localhost:8671/bookings?email=john@example.com"
```

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
omnify/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── database.py          # Database operations
├── services.py          # Business logic
├── utils.py             # Utility functions
├── tests/               # Unit tests
│   ├── test_api.py
│   └── test_services.py
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Timezone Management

- All classes are created in IST (UTC+5:30)
- The API automatically handles timezone conversions
- When timezone changes, all slots are updated accordingly

## Error Handling

The API handles various error cases:
- Invalid class ID
- No available slots
- Invalid email format
- Missing required fields
- Duplicate bookings
- Past class dates 