import io
from flask import Blueprint, make_response, render_template, request, redirect, url_for, flash, jsonify, send_file, session, current_app
from flask_login import login_required, current_user
from app.utils.auth_helper import role_required
from app.forms import FlightSearchForm, PassengerInfoForm, PaymentForm
from app.models import (
    User, Passenger, Airline, Airport, Aircraft, FlightTemplate, Flight, 
    Price, Seat, Reservation, ReservationSeat, Invoice, Discount,
    SeatClass, SeatPosition, ReservationStatus, TripType, FlightType
)
from sqlalchemy.orm import aliased
from app import db
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, cast, Date, text
import json
from werkzeug.datastructures import MultiDict

from app.utils.pdf_generator import generate_invoice_pdf, generate_ticket_pdf

bp = Blueprint('passenger', __name__, url_prefix='/passenger')

# Dashboard route
@bp.route('/dashboard', endpoint='dashboard')
@login_required
@role_required('passenger')
def passenger_dashboard():
    # Get user's recent reservations
    recent_reservations = Reservation.query.filter_by(user_id=current_user.user_id).order_by(Reservation.reservation_date.desc()).limit(5).all()
    
    # Get upcoming flights
    upcoming_flights = []
    for reservation in recent_reservations:
        if reservation.status == ReservationStatus.Confirmed:
            for reservation_seat in reservation.reservation_seats:
                if reservation_seat.flight.departure_datetime > datetime.utcnow():
                    upcoming_flights.append({
                        'reservation': reservation,
                        'flight': reservation_seat.flight,
                        'passenger' :Passenger.query.get(reservation_seat.passenger_id)

                    })
    
    return render_template('passenger/dashboard.html', 
                         user=current_user, 
                         recent_reservations=recent_reservations,
                         upcoming_flights=upcoming_flights)



@bp.route('/search', methods=['GET', 'POST'])
@login_required
@role_required('passenger')
def search_flights():
    form = FlightSearchForm()

    # ✅ FIX 1: Always populate flight_type choices before validation
    form.flight_type.choices = [
    ('domestic', 'Domestic'),
    ('international', 'International')
    ]   


    # Populate static choices
    airlines = Airline.query.all()
    form.preferred_airline.choices = [(-1, 'Any Airline')] + [
        (a.airline_id, f"{a.name} ({a.IATA_code})") for a in airlines
    ]

    # Populate country dropdowns
    countries = db.session.query(Airport.country).distinct().all()
    country_choices = [('', 'Select Country')] + [(c[0], c[0]) for c in countries]
    form.departure_country.choices = country_choices
    form.arrival_country.choices = country_choices

    # Initialize city and airport dropdowns with empty choices
    form.departure_city.choices = [('', 'Select City')]
    form.arrival_city.choices = [('', 'Select City')]
    form.departure_airport.choices = [(-1, 'Select Airport')]
    form.arrival_airport.choices = [(-1, 'Select Airport')]

    # Session restore (GET only)
    search_data = session.get('search_data', {})
    if search_data and request.method == 'GET':
        for field_name, field_obj in form._fields.items():  # ✅ unpack name and object
            if field_name in search_data and field_name != 'csrf_token':
                value = search_data[field_name]
                # ✅ FIX: convert string dates back to date objects
                if field_name in ('departure_date', 'return_date') and value:
                    try:
                        field_obj.data = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        field_obj.data = None
                else:
                    field_obj.data = value
        # Restore dropdowns
        if search_data.get('departure_country'):
            dep_cities = db.session.query(Airport.city).filter(
                Airport.country == search_data['departure_country']
            ).distinct().all()
            form.departure_city.choices = [('', 'Select City')] + [(c[0], c[0]) for c in dep_cities]

        if search_data.get('arrival_country'):
            arr_cities = db.session.query(Airport.city).filter(
                Airport.country == search_data['arrival_country']
            ).distinct().all()
            form.arrival_city.choices = [('', 'Select City')] + [(c[0], c[0]) for c in arr_cities]

        if search_data.get('departure_city'):
            dep_airports = Airport.query.filter(Airport.city == search_data['departure_city']).all()
            form.departure_airport.choices = [(-1, 'Select Airport')] + [
                (a.airport_id, f"{a.name} ({a.IATA_code})") for a in dep_airports
            ]

        if search_data.get('arrival_city'):
            arr_airports = Airport.query.filter(Airport.city == search_data['arrival_city']).all()
            form.arrival_airport.choices = [(-1, 'Select Airport')] + [
                (a.airport_id, f"{a.name} ({a.IATA_code})") for a in arr_airports
            ]

    # POST request: handle form data
    if request.method == 'POST':
        dep_country = request.form.get('departure_country')
        arr_country = request.form.get('arrival_country')

        # ✅ FIX 2: If domestic, enforce same country for arrival
        if form.flight_type.data == 'Domestic':
            arr_country = dep_country
            form.arrival_country.data = dep_country  # ensure WTForms sees same value

        # Populate cities based on selected countries
        if dep_country:
            dep_cities = db.session.query(Airport.city).filter(
                Airport.country == dep_country
            ).distinct().all()
            form.departure_city.choices = [('', 'Select City')] + [(c[0], c[0]) for c in dep_cities]

        if arr_country:
            arr_cities = db.session.query(Airport.city).filter(
                Airport.country == arr_country
            ).distinct().all()
            form.arrival_city.choices = [('', 'Select City')] + [(c[0], c[0]) for c in arr_cities]

        # Populate airports based on cities
        dep_city = request.form.get('departure_city')
        arr_city = request.form.get('arrival_city')

        if dep_city:
            dep_airports = Airport.query.filter(Airport.city == dep_city).all()
            form.departure_airport.choices = [(-1, 'Select Airport')] + [
                (a.airport_id, f"{a.name} ({a.IATA_code})") for a in dep_airports
            ]

        if arr_city:
            arr_airports = Airport.query.filter(Airport.city == arr_city).all()
            form.arrival_airport.choices = [(-1, 'Select Airport')] + [
                (a.airport_id, f"{a.name} ({a.IATA_code})") for a in arr_airports
            ]

        # Debug alert (instead of print) — you can remove later
        # ✅ FIX 3: Replace print with flashing message for frontend
        from flask import flash
        flash(f"Form validation: {form.validate_on_submit()}, Errors: {form.errors}")

        if form.validate_on_submit():
            def parse_int(value):
                try:
                    if value and int(value) > 0:
                        return int(value)
                    return None
                except:
                    return None

            def parse_float(value):
                try:
                    if value and float(value) > 0:
                        return float(value)
                    return None
                except:
                    return None

            search_data = {
                'departure_country': form.departure_country.data,
                'departure_city': form.departure_city.data,
                'departure_airport_id': parse_int(form.departure_airport.data),
                'arrival_country': form.arrival_country.data,
                'arrival_city': form.arrival_city.data,
                'arrival_airport_id': parse_int(form.arrival_airport.data),
                'departure_date': form.departure_date.data.strftime('%Y-%m-%d'),
                'return_date': form.return_date.data.strftime('%Y-%m-%d') if form.return_date.data else None,
                'trip_type': form.trip_type.data,
                'passengers': form.passengers.data,
                'seat_class': form.seat_class.data,
                'seat_preference': form.seat_preference.data or None,
                'flight_type': form.flight_type.data,
                'preferred_airline_id': parse_int(form.preferred_airline.data),
                'departure_time_range': form.departure_time_range.data or None,
                'return_time_range': form.return_time_range.data or None,
                'max_budget': parse_float(form.max_budget.data),
                'show_discounted_only': form.show_discounted_only.data,
                'sort_by': form.sort_by.data
            }

            # Add airport names for display
            if parse_int(form.departure_airport.data):
                departure_airport = Airport.query.get(parse_int(form.departure_airport.data))
                if departure_airport:
                    search_data['departure_airport'] = departure_airport.name
            else:
                search_data['departure_airport'] = form.departure_city.data

            if parse_int(form.arrival_airport.data):
                arrival_airport = Airport.query.get(parse_int(form.arrival_airport.data))
                if arrival_airport:
                    search_data['arrival_airport'] = arrival_airport.name
            else:
                search_data['arrival_airport'] = form.arrival_city.data

            # Store search data in session
            session['search_data'] = search_data
            return redirect(url_for('passenger.search_results'))

    return render_template('passenger/search.html', form=form)



# AJAX route to get cities for a country
@bp.route('/get-cities/<country>')
@login_required
@role_required('passenger')
def get_cities(country):
    cities = db.session.query(Airport.city).filter(Airport.country == country).distinct().all()
    return jsonify([city[0] for city in cities])

# AJAX route to get airports for a city
@bp.route('/get-airports/<city>')
@login_required
@role_required('passenger')
def get_airports(city):
    airports = Airport.query.filter(Airport.city == city).all()
    return jsonify([{'id': a.airport_id, 'name': f"{a.name} ({a.IATA_code})"} for a in airports])



@bp.route('/search/results', methods=['GET', 'POST'])
@login_required
@role_required('passenger')
def search_results():
    search_data = session.get('search_data')
    if not search_data:
        flash('No search data found. Please search for flights first.', 'warning')
        return redirect(url_for('passenger.search_flights'))

    # Aliases for joins
    FT = aliased(FlightTemplate)
    AL = aliased(Airline)
    AP_dep = aliased(Airport)
    AP_arr = aliased(Airport)
    PR = aliased(Price)
    DI = aliased(Discount)

    # Build base query
    query = Flight.query.join(FT).join(AL)

    # Departure date filter
    try:
        departure_date = datetime.strptime(search_data['departure_date'], '%Y-%m-%d').date()
        query = query.filter(cast(Flight.departure_datetime, Date) == departure_date)
    except (ValueError, KeyError):
        flash('Invalid departure date.', 'danger')
        return redirect(url_for('passenger.search_flights'))

    # Departure airport/city
    dep_airport_id = int(search_data.get('departure_airport_id') or 0)
    if dep_airport_id > 0:
        query = query.filter(FT.departure_airport_id == dep_airport_id)
    elif search_data.get('departure_city'):
        dep_ids = [a.airport_id for a in Airport.query.filter(Airport.city == search_data['departure_city']).all()]
        if dep_ids:
            query = query.filter(FT.departure_airport_id.in_(dep_ids))

    # Arrival airport/city
    arr_airport_id = int(search_data.get('arrival_airport_id') or 0)
    if arr_airport_id > 0:
        query = query.filter(FT.arrival_airport_id == arr_airport_id)
    elif search_data.get('arrival_city'):
        arr_ids = [a.airport_id for a in Airport.query.filter(Airport.city == search_data['arrival_city']).all()]
        if arr_ids:
            query = query.filter(FT.arrival_airport_id.in_(arr_ids))

    # Flight type (enum by value)
    if search_data.get('flight_type'):
        try:
            flight_type = FlightType(search_data['flight_type'].capitalize())
            query = query.filter(FT.flight_type == flight_type)
        except ValueError:
            pass

    # Preferred airline
    airline_id = int(search_data.get('preferred_airline_id') or 0)
    if airline_id > 0:
        query = query.filter(FT.airline_id == airline_id)

    # Departure time range
    dep_range = search_data.get('departure_time_range')
    if dep_range == 'morning':
        query = query.filter(FT.departure_airport.has(Airport.city != None))  # Dummy join to avoid errors
        query = query.filter(cast(Flight.departure_datetime, Date) != None)
        query = query.filter(FT.departure_airport_id != None)  # Replace with actual time column if exists
    elif dep_range in ['afternoon', 'evening', 'night']:
        # Replace with actual time logic if your model stores departure_time separately
        pass

    # Budget filter
    if search_data.get('max_budget'):
        try:
            max_budget = float(search_data['max_budget'])
            seat_class = search_data.get('seat_class', 'economy').lower()
            query = query.join(PR)
            if seat_class == 'economy':
                query = query.filter(PR.economy_price <= max_budget)
            elif seat_class == 'business':
                query = query.filter(PR.business_price <= max_budget)
            elif seat_class == 'first':
                query = query.filter(PR.first_price <= max_budget)
        except ValueError:
            pass

    # Discount filter
    if search_data.get('show_discounted_only'):
        query = query.join(DI)

    # Sorting
    sort_by = search_data.get('sort_by', 'departure_time')
    if sort_by == 'price':
        seat_class = search_data.get('seat_class', 'economy').lower()
        query = query.join(PR)
        if seat_class == 'economy':
            query = query.order_by(PR.economy_price.asc())
        elif seat_class == 'business':
            query = query.order_by(PR.business_price.asc())
        elif seat_class == 'first':
            query = query.order_by(PR.first_price.asc())
    elif sort_by == 'duration':
        query = query.order_by(FT.duration.asc())
    else:  # default departure_time
        query = query.order_by(Flight.departure_datetime.asc())

    flights = query.all()

    # Return flights (round-trip)
    return_flights = []
    if search_data.get('trip_type') == 'round_trip' and search_data.get('return_date'):
        try:
            return_date = datetime.strptime(search_data['return_date'], '%Y-%m-%d').date()
            return_query = Flight.query.join(FT).join(AL)
            return_query = return_query.filter(cast(Flight.departure_datetime, Date) == return_date)

            # Swap departure/arrival filters for return
            if arr_airport_id > 0:
                return_query = return_query.filter(FT.departure_airport_id == arr_airport_id)
            elif search_data.get('arrival_city'):
                arr_ids = [a.airport_id for a in Airport.query.filter(Airport.city == search_data['arrival_city']).all()]
                if arr_ids:
                    return_query = return_query.filter(FT.departure_airport_id.in_(arr_ids))

            if dep_airport_id > 0:
                return_query = return_query.filter(FT.arrival_airport_id == dep_airport_id)
            elif search_data.get('departure_city'):
                dep_ids = [a.airport_id for a in Airport.query.filter(Airport.city == search_data['departure_city']).all()]
                if dep_ids:
                    return_query = return_query.filter(FT.arrival_airport_id.in_(dep_ids))

            # Apply same airline / flight type / budget / discount filters
            if search_data.get('flight_type'):
                try:
                    flight_type = FlightType(search_data['flight_type'].capitalize())
                    return_query = return_query.filter(FT.flight_type == flight_type)
                except ValueError:
                    pass

            if airline_id > 0:
                return_query = return_query.filter(FT.airline_id == airline_id)

            if search_data.get('max_budget'):
                return_query = return_query.join(PR)
                if seat_class == 'economy':
                    return_query = return_query.filter(PR.economy_price <= max_budget)
                elif seat_class == 'business':
                    return_query = return_query.filter(PR.business_price <= max_budget)
                elif seat_class == 'first':
                    return_query = return_query.filter(PR.first_price <= max_budget)

            if search_data.get('show_discounted_only'):
                return_query = return_query.join(DI)

            # Sorting
            if sort_by == 'price':
                if seat_class == 'economy':
                    return_query = return_query.order_by(PR.economy_price.asc())
                elif seat_class == 'business':
                    return_query = return_query.order_by(PR.business_price.asc())
                elif seat_class == 'first':
                    return_query = return_query.order_by(PR.first_price.asc())
            elif sort_by == 'duration':
                return_query = return_query.order_by(FT.duration.asc())
            else:
                return_query = return_query.order_by(Flight.departure_datetime.asc())

            return_flights = return_query.all()
        except ValueError:
            pass

    return render_template(
        'passenger/search_results.html',
        flights=flights,
        return_flights=return_flights,
        search_data=search_data
    )


# Book flight route
@bp.route('/book/<int:flight_id>', methods=['GET', 'POST'])
@login_required
@role_required('passenger')
def book_flight(flight_id):

    flight = Flight.query.get_or_404(flight_id)
    search_data = json.loads(request.args.get('search_data', '{}'))

    if not search_data:
        flash('Please search for flights first.', 'warning')
        return redirect(url_for('passenger.search_flights'))
    
    # Calculate pricing
    base_price = flight.flight_template.base_price
    if search_data['seat_class'] == SeatClass.Business.value:
        base_price *= 2.5
    elif search_data['seat_class'] == SeatClass.First.value:
        base_price *= 4.0
    
    discount_percentage = 0
    if flight.discounts:
        discount_percentage = flight.discounts[0].discount_percentage
    
    discount_amount = base_price * (discount_percentage / 100)
    service_fee = base_price * 0.02
    final_price = base_price + service_fee - discount_amount
    total_price = final_price * search_data['passengers']
    
    if request.method == 'POST':
        passenger_forms = []
        valid = True
        for i in range(search_data['passengers']):
            form = PassengerInfoForm(request.form, prefix=str(i))
            passenger_forms.append(form)
            if not form.validate():
                valid = False
                print(f"Form {i} errors: {form.errors}") 

        
        if valid:
            passenger_data = []
            for form in passenger_forms:
                passenger_data.append({
                    'first_name': form.first_name.data,
                    'last_name': form.last_name.data,
                    'gender': form.gender.data,
                    'age': form.age.data,
                    'passport_no': form.passport_no.data,
                    'contact_number': form.contact_number.data,
                })
            
            session_data = {
                'flight_id': flight_id,
                'search_data': search_data,
                'passenger_data': passenger_data,
                'total_price': total_price,
            }
            return redirect(url_for('passenger.select_seats', session_data=json.dumps(session_data)))
        
        # If form invalid, render template with errors
        return render_template('passenger/book_flight.html',
                               flight=flight,
                               search_data=search_data,
                               base_price=base_price,
                               discount_percentage=discount_percentage,
                               service_fee=service_fee,
                               final_price=final_price,
                               total_price=total_price,
                               passenger_forms=passenger_forms)
    
    # For GET requests, create empty forms and render
    passenger_forms = [PassengerInfoForm(prefix=str(i)) for i in range(search_data['passengers'])]

    return render_template('passenger/book_flight.html',
                           flight=flight,
                           search_data=search_data,
                           base_price=base_price,
                           discount_percentage=discount_percentage,
                           service_fee=service_fee,
                           final_price=final_price,
                           total_price=total_price,
                           passenger_forms=passenger_forms)

# Select seats route
@bp.route('/select-seats', methods=['GET', 'POST'])
@login_required
@role_required('passenger')
def select_seats():
    session_data = json.loads(request.args.get('session_data', '{}'))
    
    if not session_data:
        flash('Please book a flight first.', 'warning')
        return redirect(url_for('passenger.search_flights'))
    
    flight = Flight.query.get_or_404(session_data['flight_id'])
    search_data = session_data['search_data']
    
    # Get available seats for the selected class
    available_seats = Seat.query.filter(
        and_(
            Seat.aircraft_id == flight.flight_template.aircraft_id,
            Seat.class_ == search_data['seat_class']
        )
    ).all()
    
    # Filter out already booked seats
    booked_seat_ids = [rs.seat_id for rs in flight.reservations_seats]
    available_seats = [seat for seat in available_seats if seat.seat_id not in booked_seat_ids]
    
    if request.method == 'POST':
        selected_seats_str = request.form.get('selected_seats', '')
        selected_seats = selected_seats_str.split(',') if selected_seats_str else []
        
        if len(selected_seats) == len(session_data['passenger_data']):
            session_data['selected_seats'] = selected_seats
            return redirect(url_for('passenger.payment', session_data=json.dumps(session_data)))
        else:
            flash('Please select seats for all passengers.', 'warning')

        
    return render_template('passenger/select_seats.html', 
                        flight=flight,
                        available_seats=available_seats,
                        session_data=session_data)

# Payment route
@bp.route('/payment', methods=['GET', 'POST'])
@login_required
@role_required('passenger')
def payment():
    session_data = json.loads(request.args.get('session_data', '{}'))
    
    if not session_data:
        flash('Please complete booking steps first.', 'warning')
        return redirect(url_for('passenger.search_flights'))
    
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Process payment (dummy implementation)
        try:
            # Create passengers
            passengers = []
            for passenger_info in session_data['passenger_data']:
                passenger = Passenger(**passenger_info)
                db.session.add(passenger)
                db.session.flush()  # Get the ID
                passengers.append(passenger)
            
            trip_type_map = {
                'one-way': 'One_way',
                'round-trip': 'Round_trip'
            }

            trip_type_value = trip_type_map.get(session_data['search_data']['trip_type'], 'One_way') 
            
            flight_type_map = {
            'economy': 'Economy',
            'business': 'Business',
            'first-class': 'First_Class'
            }
            

            
            # Create reservation
            reservation = Reservation(
                user_id=current_user.user_id,
                total_price=session_data['total_price'],
                payment_method='Credit Card',
                status=ReservationStatus.Confirmed,
                trip_type=trip_type_value
            )
            db.session.add(reservation)
            db.session.flush()
            
            # Create reservation seats
            flight = Flight.query.get(session_data['flight_id'])
            for i, seat_id in enumerate(session_data['selected_seats']):
                reservation_seat = ReservationSeat(
                    flight_id=flight.flight_id,
                    reservation_id=reservation.reservation_id,
                    passenger_id=passengers[i].passenger_id,
                    seat_id=int(seat_id)
                )
                db.session.add(reservation_seat)
            
            # Create invoice
            invoice = Invoice(
                reservation_id=reservation.reservation_id,
                amount=session_data['total_price']
            )
            db.session.add(invoice)
            
            db.session.commit()
            
            flash('Booking confirmed! Your ticket has been generated.', 'success')
            return redirect(url_for('passenger.view_ticket', reservation_id=reservation.reservation_id))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during booking. Please try again.', 'danger')
            print(f"Booking error: {e}") 
    
    return render_template('passenger/payment.html', 
                         form=form, 
                         session_data=session_data)

# View ticket page
@bp.route('/ticket/<int:reservation_id>')
@login_required
@role_required('passenger')
def view_ticket(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation_id).all()
    if not reservation_seats:
        flash('No seats found for this reservation.', 'danger')
        return redirect(url_for('passenger.dashboard'))

    passenger_seat_pairs = []
    flight = None

    for rs in reservation_seats:
        flight = Flight.query.get_or_404(rs.flight_id)
        passenger = Passenger.query.get_or_404(rs.passenger_id)
        seat = Seat.query.get_or_404(rs.seat_id)
        passenger_seat_pairs.append({"passenger": passenger, "seat": seat})

    flights_info = [{
        "passenger_seat_pairs": passenger_seat_pairs,
        "flight": flight
    }]
    return render_template(
        'passenger/ticket.html',
        reservation=reservation,
        flights_info=flights_info,
        flight=flight
    )


# Download ticket PDF
@bp.route('/ticket/<int:reservation_id>/download')
@login_required
@role_required('passenger')
def download_ticket(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation_id).all()
    if not reservation_seats:
        flash('No seats found for this reservation.', 'danger')
        return redirect(url_for('passenger.dashboard'))

    passenger_seat_pairs = []
    flight = None

    for rs in reservation_seats:
        flight = Flight.query.get_or_404(rs.flight_id)
        passenger = Passenger.query.get_or_404(rs.passenger_id)
        seat = Seat.query.get_or_404(rs.seat_id)
        passenger_seat_pairs.append({"passenger": passenger, "seat": seat})

        # Generate PDF bytes
    pdf_bytes = generate_ticket_pdf(reservation, passenger_seat_pairs, flight)

    # Send PDF as downloadable file
    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"TKT-{reservation.reservation_id:06d}.pdf",
        mimetype='application/pdf'
    )



# donwload invoice route
@bp.route('/invoice/<int:reservation_id>/download')
@login_required
@role_required('passenger')
def download_invoice(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)

    if reservation.user_id != current_user.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('passenger.dashboard'))

    reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation_id).all()
    if not reservation_seats:
        flash('No seats found for this reservation.', 'danger')
        return redirect(url_for('passenger.dashboard'))

    flight = Flight.query.get(reservation_seats[0].flight_id)
    user = reservation.user  # directly from reservation relationship

    user_info = {
        'name': user.name,
        'email': user.email
    }

    pdf_bytes = generate_invoice_pdf(reservation, reservation_seats, flight, user_info)

    return send_file(
        io.BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"invoice_{reservation.reservation_id:06d}.pdf",
        mimetype='application/pdf'
    )


#view bookings route
@bp.route('/bookings')
@login_required
@role_required('passenger')
def view_bookings():
    reservations = Reservation.query.filter_by(user_id=current_user.user_id).order_by(Reservation.reservation_date.desc()).all()
    
    booking_details = []
    for reservation in reservations:
        reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation.reservation_id).all()
        for reservation_seat in reservation_seats:
            # Manually query the related passenger and seat
            passenger = Passenger.query.get(reservation_seat.passenger_id)
            seat = Seat.query.get(reservation_seat.seat_id)

            booking_details.append({
                'reservation': reservation,
                'flight': Flight.query.get(reservation_seat.flight_id),
                'passenger': passenger,
                'seat': seat,
                'can_refund': reservation.status == ReservationStatus.Confirmed and 
                             Flight.query.get(reservation_seat.flight_id).departure_datetime > datetime.utcnow()
            })
    
    return render_template('passenger/bookings.html', booking_details=booking_details)


# Refund route
@bp.route('/refund/<int:reservation_id>', methods=['POST'])
@login_required
@role_required('passenger')
def refund_booking(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    
    if reservation.user_id != current_user.user_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('passenger.view_bookings'))
    
    if reservation.status != ReservationStatus.Confirmed:
        flash('This booking cannot be refunded.', 'warning')
        return redirect(url_for('passenger.view_bookings'))
    
    # Check if flight has departed
    reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation_id).all()
    if not reservation_seats or reservation_seats[0].flight.departure_datetime <= datetime.utcnow():
        flash('Cannot refund after flight departure.', 'warning')
        return redirect(url_for('passenger.view_bookings'))
    
    try:
        # Calculate refund amount (75% of original price)
        refund_amount = reservation.total_price * 0.75
        
        # Update reservation status
        reservation.status = ReservationStatus.Refunded
        
        # Update invoice amount to reflect refund
        if reservation.invoice:
            reservation.invoice.amount = refund_amount
        
        db.session.commit()
        
        flash(f'Refund processed successfully. Refund amount: ${refund_amount:.2f}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred during refund processing.', 'danger')
    
    return redirect(url_for('passenger.view_bookings'))
