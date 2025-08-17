from app import create_app, db
from app.models import (
    User, Passenger, Airline, Airport, Aircraft, FlightTemplate,
    Flight, Price, Seat, SeatClass, SeatPosition, FlightType,
    Reservation, ReservationSeat, ReservationStatus, TripType,
    Invoice, Discount
)
from datetime import datetime, timedelta
import random

def create_test_data():
    app = create_app()

    with app.app_context():
        print("🛫 Starting test data creation...")

        # --- Admin user ---
        admin_email = "admin@skylink.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                name="Admin User",
                email=admin_email,
                role="admin"
            )
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            print(f"✅ Created admin user: {admin_email}")
        else:
            print(f"⚠️ Admin user {admin_email} already exists")

        # --- Airlines ---
        airlines_data = [
            {"name": "Pakistan International Airlines", "IATA_code": "PK", "ICAO_code": "PIA", "support_email": "support@pia.com"},
            {"name": "Emirates", "IATA_code": "EK", "ICAO_code": "UAE", "support_email": "support@emirates.com"},
            {"name": "Qatar Airways", "IATA_code": "QR", "ICAO_code": "QTR", "support_email": "support@qatarairways.com"},
            {"name": "Turkish Airlines", "IATA_code": "TK", "ICAO_code": "THY", "support_email": "support@turkishairlines.com"},
            {"name": "Etihad Airways", "IATA_code": "EY", "ICAO_code": "ETD", "support_email": "support@etihad.com"}
        ]
        for data in airlines_data:
            if not Airline.query.filter_by(IATA_code=data["IATA_code"]).first():
                db.session.add(Airline(**data))
                print(f"✅ Created airline {data['name']}")
            else:
                print(f"⚠️ Airline {data['name']} exists")

        # --- Airports ---
        airports_data = [
            {"name": "Jinnah International Airport", "city": "Karachi", "country": "Pakistan", "IATA_code": "KHI", "ICAO_code": "OPKC"},
            {"name": "Allama Iqbal International Airport", "city": "Lahore", "country": "Pakistan", "IATA_code": "LHE", "ICAO_code": "OPLA"},
            {"name": "Islamabad International Airport", "city": "Islamabad", "country": "Pakistan", "IATA_code": "ISB", "ICAO_code": "OPIS"},
            {"name": "Dubai International Airport", "city": "Dubai", "country": "UAE", "IATA_code": "DXB", "ICAO_code": "OMDB"},
            {"name": "Hamad International Airport", "city": "Doha", "country": "Qatar", "IATA_code": "DOH", "ICAO_code": "OTHH"},
            {"name": "Istanbul Airport", "city": "Istanbul", "country": "Turkey", "IATA_code": "IST", "ICAO_code": "LTFM"},
            {"name": "Abu Dhabi International Airport", "city": "Abu Dhabi", "country": "UAE", "IATA_code": "AUH", "ICAO_code": "OMAA"},
            {"name": "JFK International Airport", "city": "New York", "country": "USA", "IATA_code": "JFK", "ICAO_code": "KJFK"},
            {"name": "Heathrow Airport", "city": "London", "country": "UK", "IATA_code": "LHR", "ICAO_code": "EGLL"},
            {"name": "Charles de Gaulle Airport", "city": "Paris", "country": "France", "IATA_code": "CDG", "ICAO_code": "LFPG"}
        ]
        for data in airports_data:
            if not Airport.query.filter_by(IATA_code=data["IATA_code"]).first():
                db.session.add(Airport(**data))
                print(f"✅ Created airport {data['name']} ({data['city']})")
            else:
                print(f"⚠️ Airport {data['name']} exists")

        db.session.commit()

        # --- Aircraft ---
        aircraft_data = [
            {"model": "Boeing 777-300ER", "total_seats": 396},
            {"model": "Airbus A320neo", "total_seats": 180},
            {"model": "Boeing 787-9 Dreamliner", "total_seats": 294},
            {"model": "Airbus A350-900", "total_seats": 325},
            {"model": "Boeing 737-800", "total_seats": 189}
        ]
        airlines = Airline.query.all()
        for i, ac_data in enumerate(aircraft_data):
            if not Aircraft.query.filter_by(model=ac_data["model"]).first():
                db.session.add(Aircraft(
                    airline_id=airlines[i % len(airlines)].airline_id,
                    model=ac_data["model"],
                    total_seats=ac_data["total_seats"]
                ))
                print(f"✅ Created aircraft {ac_data['model']}")
            else:
                print(f"⚠️ Aircraft {ac_data['model']} exists")

        db.session.commit()

        # --- Flight Templates ---
        templates_data = [
            {"flight_number": "PK-101", "dep": "KHI", "arr": "LHE", "duration": "02:30:00", "price": 15000, "type": FlightType.Domestic},
            {"flight_number": "PK-201", "dep": "KHI", "arr": "DXB", "duration": "03:15:00", "price": 45000, "type": FlightType.International},
            {"flight_number": "EK-301", "dep": "DXB", "arr": "LHR", "duration": "07:30:00", "price": 85000, "type": FlightType.International},
            {"flight_number": "QR-401", "dep": "DOH", "arr": "JFK", "duration": "14:00:00", "price": 120000, "type": FlightType.International}
        ]
        aircrafts = Aircraft.query.all()
        airports_map = {a.IATA_code: a for a in Airport.query.all()}
        for i, t in enumerate(templates_data):
            if not FlightTemplate.query.filter_by(flight_number=t["flight_number"]).first():
                db.session.add(FlightTemplate(
                    airline_id=aircrafts[i % len(aircrafts)].airline_id,
                    aircraft_id=aircrafts[i % len(aircrafts)].aircraft_id,
                    flight_number=t["flight_number"],
                    departure_airport_id=airports_map[t["dep"]].airport_id,
                    arrival_airport_id=airports_map[t["arr"]].airport_id,
                    duration=datetime.strptime(t["duration"], "%H:%M:%S").time(),
                    base_price=t["price"],
                    flight_type=t["type"]
                ))
                print(f"✅ Created flight template {t['flight_number']}")
            else:
                print(f"⚠️ Flight template {t['flight_number']} exists")

        db.session.commit()

        # --- Prices ---
        for template in FlightTemplate.query.all():
            if not Price.query.filter_by(flight_template_id=template.flight_template_id).first():
                db.session.add(Price(
                    flight_template_id=template.flight_template_id,
                    economy_price=template.base_price,
                    business_price=template.base_price * 2.5,
                    first_price=template.base_price * 4
                ))
                print(f"✅ Prices set for {template.flight_number}")

        db.session.commit()

        # --- Seats ---
        for aircraft in Aircraft.query.all():
            if Seat.query.filter_by(aircraft_id=aircraft.aircraft_id).first():
                print(f"⚠️ Seats exist for {aircraft.model}")
                continue

            econ = int(aircraft.total_seats * 0.7)
            bus = int(aircraft.total_seats * 0.2)
            first = aircraft.total_seats - econ - bus

            for i in range(econ):
                db.session.add(Seat(
                    aircraft_id=aircraft.aircraft_id,
                    seat_number=f"E{i+1}",
                    class_=SeatClass.Economy,
                    position=random.choice(list(SeatPosition))
                ))
            for i in range(bus):
                db.session.add(Seat(
                    aircraft_id=aircraft.aircraft_id,
                    seat_number=f"B{i+1}",
                    class_=SeatClass.Business,
                    position=random.choice(list(SeatPosition))
                ))
            for i in range(first):
                db.session.add(Seat(
                    aircraft_id=aircraft.aircraft_id,
                    seat_number=f"F{i+1}",
                    class_=SeatClass.First,
                    position=random.choice(list(SeatPosition))
                ))

            print(f"✅ Created seats for {aircraft.model}")

        db.session.commit()

        # --- Scheduled Flights (30 days) ---
        base_date = datetime.now()
        for template in FlightTemplate.query.all():
            if Flight.query.filter_by(flight_template_id=template.flight_template_id).count() >= 30:
                print(f"⚠️ Flights exist for {template.flight_number}")
                continue
            for day in range(30):
                dep = base_date + timedelta(days=day, hours=8)
                arr = dep + timedelta(hours=template.duration.hour, minutes=template.duration.minute)
                db.session.add(Flight(
                    flight_template_id=template.flight_template_id,
                    departure_datetime=dep,
                    arrival_datetime=arr,
                    timezone_diff=0,
                    is_active=True
                ))
            print(f"✅ Created flights for {template.flight_number}")

        db.session.commit()

        # --- Users & Passengers ---
        passenger_data = [
            ("John", "Doe", "Male", 29, "P1234567", "+1234567890", "john@example.com"),
            ("Jane", "Smith", "Female", 32, "P2345678", "+1234567891", "jane@example.com"),
            ("Ali", "Khan", "Male", 40, "P3456789", "+923001234567", "ali@example.com")
        ]
        passengers = []
        for first, last, gender, age, passport, phone, email in passenger_data:
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(name=f"{first} {last}", email=email, role="passenger")
                user.set_password("password123")
                db.session.add(user)
                db.session.flush()
            passenger = Passenger.query.filter_by(passport_no=passport).first()
            if not passenger:
                passenger = Passenger(
                    first_name=first,
                    last_name=last,
                    gender=gender,
                    age=age,
                    passport_no=passport,
                    contact_number=phone
                )
                db.session.add(passenger)
            passengers.append((user, passenger))
            print(f"✅ Passenger {first} {last} ready")

        db.session.commit()

        # --- Reservations ---
        flights = Flight.query.limit(10).all()
        seats = Seat.query.limit(50).all()
        for i, (user, passenger) in enumerate(passengers):
            if Reservation.query.filter_by(user_id=user.user_id).first():
                print(f"⚠️ Reservation exists for {user.email}")
                continue
            flight = flights[i % len(flights)]
            seat = seats[i % len(seats)]
            price = Price.query.filter_by(flight_template_id=flight.flight_template_id).first().economy_price

            reservation = Reservation(
                user_id=user.user_id,
                total_price=price,
                payment_method=random.choice(["Credit Card", "PayPal", "Bank Transfer"]),
                status=ReservationStatus.Confirmed,
                trip_type=TripType.One_way
            )
            db.session.add(reservation)
            db.session.flush()

            db.session.add(ReservationSeat(
                flight_id=flight.flight_id,
                reservation_id=reservation.reservation_id,
                passenger_id=passenger.passenger_id,
                seat_id=seat.seat_id
            ))

            db.session.add(Invoice(
                reservation_id=reservation.reservation_id,
                amount=price
            ))

            if random.random() < 0.3:
                db.session.add(Discount(
                    flight_id=flight.flight_id,
                    discount_percentage=random.choice([5, 10, 15])
                ))

            print(f"✅ Reservation for {user.email} on {flight.flight_template.flight_number}")

        db.session.commit()

        print("\n🎉 Test data creation complete!")

if __name__ == "__main__":
    create_test_data()
