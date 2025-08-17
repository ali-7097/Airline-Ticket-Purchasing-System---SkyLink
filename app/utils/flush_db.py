import sys
import os

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app, db
from app.models import (
    User,
    Passenger,
    Airline,
    Aircraft,
    Airport,
    FlightTemplate,
    Flight,
    Price,
    Seat,
    Reservation,
    ReservationSeat,
    Invoice,
    Discount,
)

app = create_app()  # create the Flask app instance

def delete_all_data():
    db.session.query(ReservationSeat).delete()
    db.session.query(Invoice).delete()
    db.session.query(Discount).delete()
    db.session.query(Reservation).delete()
    db.session.query(Flight).delete()
    db.session.query(Price).delete()
    db.session.query(Seat).delete()
    db.session.query(FlightTemplate).delete()
    db.session.query(Aircraft).delete()
    db.session.query(Passenger).delete()
    db.session.query(Airport).delete()
    db.session.query(Airline).delete()
    db.session.query(User).delete()

    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        delete_all_data()
        print("All data deleted successfully.")
# This script deletes all data from the database tables defined in the models.