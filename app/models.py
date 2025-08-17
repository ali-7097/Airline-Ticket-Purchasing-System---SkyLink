from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Enums
class SeatClass(Enum):
    Economy = "Economy"
    Business = "Business"
    First = "First"

class SeatPosition(Enum):
    Window = "Window"
    Aisle = "Aisle"
    Middle = "Middle"

class ReservationStatus(Enum):
    Confirmed = "Confirmed"
    Cancelled = "Cancelled"
    Refunded = "Refunded"

class TripType(Enum):
    One_way = "one-way"
    Round_trip = "round-trip"

class FlightType(Enum):
    Domestic = "Domestic"
    International = "International"

# 1. Users
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='passenger')

    reservations = db.relationship("Reservation", backref="user", lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.email}>"
    
    def get_id(self):
        return str(self.user_id)  


# 2. Passengers
class Passenger(db.Model):
    __tablename__ = 'passengers'
    passenger_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    passport_no = db.Column(db.String(50), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)

# 3. Airlines
class Airline(db.Model):
    __tablename__ = 'airlines'
    airline_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    IATA_code = db.Column(db.String(10), nullable=False)
    ICAO_code = db.Column(db.String(10), nullable=False)
    support_email = db.Column(db.String(120), nullable=False)

    aircrafts = db.relationship("Aircraft", backref="airline", lazy=True)
    flight_templates = db.relationship("FlightTemplate", backref="airline", lazy=True)

# 4. Aircrafts
class Aircraft(db.Model):
    __tablename__ = 'aircrafts'
    aircraft_id = db.Column(db.Integer, primary_key=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.airline_id'), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)

    seats = db.relationship("Seat", backref="aircraft", lazy=True)
    flight_templates = db.relationship("FlightTemplate", backref="aircraft", lazy=True)

# 5. Airports
class Airport(db.Model):
    __tablename__ = 'airports'
    airport_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    IATA_code = db.Column(db.String(10), nullable=False)
    ICAO_code = db.Column(db.String(10), nullable=False)

# 6. Flight Templates
class FlightTemplate(db.Model):
    __tablename__ = 'flight_template'
    flight_template_id = db.Column(db.Integer, primary_key=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.airline_id'), nullable=False)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircrafts.aircraft_id'), nullable=False)
    flight_number = db.Column(db.String(10), nullable=False)
    departure_airport_id = db.Column(db.Integer, db.ForeignKey('airports.airport_id'), nullable=False)
    arrival_airport_id = db.Column(db.Integer, db.ForeignKey('airports.airport_id'), nullable=False)
    duration = db.Column(db.Time, nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    flight_type = db.Column(db.Enum(FlightType), nullable=False)

    prices = db.relationship("Price", backref="flight_template", uselist=False)
    flights = db.relationship("Flight", backref="flight_template", lazy=True)
    
    # Add relationships to airports
    departure_airport = db.relationship("Airport", foreign_keys=[departure_airport_id], backref="departure_templates")
    arrival_airport = db.relationship("Airport", foreign_keys=[arrival_airport_id], backref="arrival_templates")

# 7. Flights (Scheduled)
class Flight(db.Model):
    __tablename__ = 'flights'
    flight_id = db.Column(db.Integer, primary_key=True)
    flight_template_id = db.Column(db.Integer, db.ForeignKey('flight_template.flight_template_id'), nullable=False)
    departure_datetime = db.Column(db.DateTime, nullable=False)
    arrival_datetime = db.Column(db.DateTime, nullable=False)
    timezone_diff = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    reservations_seats = db.relationship("ReservationSeat", backref="flight", lazy=True)
    discounts = db.relationship("Discount", backref="flight", lazy=True)

# 8. Prices
class Price(db.Model):
    __tablename__ = 'prices'
    price_id = db.Column(db.Integer, primary_key=True)
    flight_template_id = db.Column(db.Integer, db.ForeignKey('flight_template.flight_template_id'), nullable=False, unique=True)
    economy_price = db.Column(db.Float, nullable=False)
    business_price = db.Column(db.Float, nullable=False)
    first_price = db.Column(db.Float, nullable=False)

# 9. Seats
class Seat(db.Model):
    __tablename__ = 'seats'
    seat_id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircrafts.aircraft_id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    class_ = db.Column(db.Enum(SeatClass), nullable=False)
    position = db.Column(db.Enum(SeatPosition), nullable=False)

# 10. Reservations
class Reservation(db.Model):
    __tablename__ = 'reservations'
    reservation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum(ReservationStatus), nullable=False)
    trip_type = db.Column(db.Enum(TripType), nullable=False, default=TripType.One_way)

    invoice = db.relationship("Invoice", backref="reservation", uselist=False)
    reservation_seats = db.relationship("ReservationSeat", backref="reservation", lazy=True)

# 11. Reservation Seats
class ReservationSeat(db.Model):
    __tablename__ = 'reservation_seats'
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.flight_id'), primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.reservation_id'), primary_key=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.passenger_id'), primary_key=True)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.seat_id'), nullable=False)

# 12. Invoices
class Invoice(db.Model):
    __tablename__ = 'invoices'
    invoice_id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey('reservations.reservation_id'), nullable=False, unique=True)
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)

# 13. Discounts
class Discount(db.Model):
    __tablename__ = 'discounts'
    discount_id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.flight_id'), nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
