import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
from utils import IST, convert_to_ist, get_current_ist_time, log_error


class Database:
    """SQLite database manager for fitness studio booking system"""
    
    def __init__(self, db_path: str = "fitness_studio.db"):
        self.db_path = db_path
        self.init_database()
        # Only seed data if tables are empty
        self.seed_data()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create classes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_time TEXT NOT NULL,
                instructor TEXT NOT NULL,
                available_slots INTEGER NOT NULL,
                total_slots INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create bookings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                client_email TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def seed_data(self):
        """Seed database with sample fitness classes"""
        # Check if data already exists
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM classes")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Sample classes data
        current_time = get_current_ist_time()
        sample_classes = [
            {
                'name': 'Yoga',
                'date_time': (current_time + timedelta(days=1, hours=10)).isoformat(),
                'instructor': 'Sarah Johnson',
                'available_slots': 20,
                'total_slots': 20
            },
            {
                'name': 'Zumba',
                'date_time': (current_time + timedelta(days=1, hours=18)).isoformat(),
                'instructor': 'Mike Rodriguez',
                'available_slots': 15,
                'total_slots': 15
            },
            {
                'name': 'HIIT',
                'date_time': (current_time + timedelta(days=2, hours=7)).isoformat(),
                'instructor': 'Emma Wilson',
                'available_slots': 12,
                'total_slots': 12
            },
            {
                'name': 'Pilates',
                'date_time': (current_time + timedelta(days=2, hours=16)).isoformat(),
                'instructor': 'David Chen',
                'available_slots': 10,
                'total_slots': 10
            },
            {
                'name': 'Spinning',
                'date_time': (current_time + timedelta(days=3, hours=9)).isoformat(),
                'instructor': 'Lisa Thompson',
                'available_slots': 18,
                'total_slots': 18
            }
        ]
        
        # Insert sample classes
        for class_data in sample_classes:
            cursor.execute('''
                INSERT INTO classes (name, date_time, instructor, available_slots, total_slots)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                class_data['name'],
                class_data['date_time'],
                class_data['instructor'],
                class_data['available_slots'],
                class_data['total_slots']
            ))
        
        conn.commit()
        conn.close()
    
    def get_all_classes(self) -> List[Dict[str, Any]]:
        """Get all upcoming classes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, date_time, instructor, available_slots, total_slots
            FROM classes
            WHERE datetime(date_time) > datetime('now')
            ORDER BY date_time
        ''')
        
        classes = []
        for row in cursor.fetchall():
            classes.append({
                'id': row['id'],
                'name': row['name'],
                'date_time': row['date_time'],
                'instructor': row['instructor'],
                'available_slots': row['available_slots'],
                'total_slots': row['total_slots']
            })
        
        conn.close()
        return classes
    
    def get_class_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """Get class by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, date_time, instructor, available_slots, total_slots
            FROM classes
            WHERE id = ?
        ''', (class_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'name': row['name'],
                'date_time': row['date_time'],
                'instructor': row['instructor'],
                'available_slots': row['available_slots'],
                'total_slots': row['total_slots']
            }
        return None
    
    def create_booking(self, class_id: int, client_name: str, client_email: str) -> Optional[int]:
        """Create a new booking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if class exists and has available slots
            cursor.execute('''
                SELECT name, date_time, available_slots
                FROM classes
                WHERE id = ? AND available_slots > 0
            ''', (class_id,))
            
            class_data = cursor.fetchone()
            if not class_data:
                conn.close()
                return None
            
            # Check if client already booked this class
            cursor.execute('''
                SELECT id FROM bookings
                WHERE class_id = ? AND client_email = ?
            ''', (class_id, client_email))
            
            if cursor.fetchone():
                conn.close()
                return None
            
            # Create booking
            cursor.execute('''
                INSERT INTO bookings (class_id, client_name, client_email, booking_date)
                VALUES (?, ?, ?, ?)
            ''', (class_id, client_name, client_email, class_data['date_time']))
            
            booking_id = cursor.lastrowid
            
            # Update available slots
            cursor.execute('''
                UPDATE classes
                SET available_slots = available_slots - 1
                WHERE id = ?
            ''', (class_id,))
            
            conn.commit()
            conn.close()
            return booking_id
            
        except Exception as e:
            log_error("Database error in create_booking", str(e))
            conn.rollback()
            conn.close()
            return None
    
    def get_bookings_by_email(self, email: str) -> List[Dict[str, Any]]:
        """Get all bookings for a specific email"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, c.name as class_name, b.client_name, b.client_email, b.booking_date
            FROM bookings b
            JOIN classes c ON b.class_id = c.id
            WHERE b.client_email = ?
            ORDER BY b.booking_date DESC
        ''', (email,))
        
        bookings = []
        for row in cursor.fetchall():
            bookings.append({
                'id': row['id'],
                'class_name': row['class_name'],
                'client_name': row['client_name'],
                'client_email': row['client_email'],
                'booking_date': row['booking_date']
            })
        
        conn.close()
        return bookings
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Get booking by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.id, c.name as class_name, b.client_name, b.client_email, b.booking_date
            FROM bookings b
            JOIN classes c ON b.class_id = c.id
            WHERE b.id = ?
        ''', (booking_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'class_name': row['class_name'],
                'client_name': row['client_name'],
                'client_email': row['client_email'],
                'booking_date': row['booking_date']
            }
        return None


# Global database instance - will be initialized when needed
db = None

def get_db():
    """Get database instance, initializing if necessary"""
    global db
    if db is None:
        db = Database()
    return db 