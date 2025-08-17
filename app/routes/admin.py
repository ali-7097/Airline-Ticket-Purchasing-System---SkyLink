from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.auth_helper import role_required
from app.forms import FlightTemplateForm, FlightForm, DiscountForm, PriceForm
from app.models import (
    User, Passenger, Airline, Airport, Aircraft, FlightTemplate, Flight, 
    Price, Seat, Reservation, ReservationSeat, Invoice, Discount,
    SeatClass, SeatPosition, ReservationStatus, TripType, FlightType
)
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    # Calculate analytics
    total_revenue = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    total_tickets = db.session.query(func.count(Reservation.reservation_id)).scalar() or 0
    total_flights = db.session.query(func.count(Flight.flight_id)).scalar() or 0
    active_flights = db.session.query(func.count(Flight.flight_id)).filter(Flight.is_active == True).scalar() or 0
    
    # Most popular routes - Fixed join ambiguity
    popular_routes = db.session.query(
        FlightTemplate.departure_airport_id,
        FlightTemplate.arrival_airport_id,
        func.count(ReservationSeat.reservation_id).label('booking_count')
    ).select_from(FlightTemplate).join(Flight, FlightTemplate.flight_template_id == Flight.flight_template_id).join(
        ReservationSeat, Flight.flight_id == ReservationSeat.flight_id
    ).group_by(
        FlightTemplate.departure_airport_id,
        FlightTemplate.arrival_airport_id
    ).order_by(func.count(ReservationSeat.reservation_id).desc()).limit(5).all()
    
    # Revenue by month (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        revenue = db.session.query(func.sum(Invoice.amount)).filter(
            and_(
                Invoice.issued_date >= month_start,
                Invoice.issued_date <= month_end
            )
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%B %Y'),
            'revenue': revenue
        })
    
    # Recent bookings
    recent_bookings = Reservation.query.order_by(Reservation.reservation_date.desc()).limit(10).all()
    
    # Flight status summary
    flight_status = {
        'active': active_flights,
        'inactive': total_flights - active_flights
    }
    
    return render_template('admin/dashboard.html', 
                         user=current_user,
                         total_revenue=total_revenue,
                         total_tickets=total_tickets,
                         total_flights=total_flights,
                         active_flights=active_flights,
                         popular_routes=popular_routes,
                         monthly_revenue=monthly_revenue,
                         recent_bookings=recent_bookings,
                         flight_status=flight_status)

@bp.route('/flights')
@login_required
@role_required('admin')
def manage_flights():
    flights = Flight.query.order_by(Flight.departure_datetime.desc()).all()
    return render_template('admin/flights.html', flights=flights)

@bp.route('/flights/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_flight():
    form = FlightForm()
    
    # Populate flight template choices
    templates = FlightTemplate.query.all()
    form.flight_template_id.choices = [(t.flight_template_id, f"{t.flight_number} - {t.departure_airport.name} to {t.arrival_airport.name}") for t in templates]
    
    if form.validate_on_submit():
        try:
            # Parse datetime strings
            departure_datetime = datetime.strptime(form.departure_datetime.data, '%Y-%m-%dT%H:%M')
            arrival_datetime = datetime.strptime(form.arrival_datetime.data, '%Y-%m-%dT%H:%M')
            
            flight = Flight(
                flight_template_id=form.flight_template_id.data,
                departure_datetime=departure_datetime,
                arrival_datetime=arrival_datetime,
                timezone_diff=form.timezone_diff.data,
                is_active=True
            )
            
            db.session.add(flight)
            db.session.commit()
            
            flash('Flight scheduled successfully!', 'success')
            return redirect(url_for('admin.manage_flights'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while scheduling the flight.', 'danger')
    
    return render_template('admin/add_flight.html', form=form)

@bp.route('/flights/<int:flight_id>/toggle', methods=['POST'])
@login_required
@role_required('admin')
def toggle_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    
    try:
        flight.is_active = not flight.is_active
        db.session.commit()
        
        status = "activated" if flight.is_active else "deactivated"
        flash(f'Flight {status} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating flight status.', 'danger')
    
    return redirect(url_for('admin.manage_flights'))

@bp.route('/flights/<int:flight_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    form = FlightForm(obj=flight)
    
    # Populate flight template choices
    templates = FlightTemplate.query.all()
    form.flight_template_id.choices = [(t.flight_template_id, f"{t.flight_number} - {t.departure_airport.name} to {t.arrival_airport.name}") for t in templates]
    
    if form.validate_on_submit():
        try:
            # Parse datetime strings
            departure_datetime = datetime.strptime(form.departure_datetime.data, '%Y-%m-%dT%H:%M')
            arrival_datetime = datetime.strptime(form.arrival_datetime.data, '%Y-%m-%dT%H:%M')
            
            flight.flight_template_id = form.flight_template_id.data
            flight.departure_datetime = departure_datetime
            flight.arrival_datetime = arrival_datetime
            flight.timezone_diff = form.timezone_diff.data
            
            db.session.commit()
            
            flash('Flight updated successfully!', 'success')
            return redirect(url_for('admin.manage_flights'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the flight.', 'danger')
    
    # Pre-populate form with current values
    form.departure_datetime.data = flight.departure_datetime.strftime('%Y-%m-%dT%H:%M')
    form.arrival_datetime.data = flight.arrival_datetime.strftime('%Y-%m-%dT%H:%M')
    
    return render_template('admin/edit_flight.html', form=form, flight=flight)

@bp.route('/templates')
@login_required
@role_required('admin')
def manage_templates():
    templates = FlightTemplate.query.all()
    return render_template('admin/templates.html', templates=templates)

@bp.route('/templates/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_template():
    form = FlightTemplateForm()
    
    # Populate choices
    airlines = Airline.query.all()
    aircrafts = Aircraft.query.all()
    airports = Airport.query.all()
    
    form.airline_id.choices = [(a.airline_id, a.name) for a in airlines]
    form.aircraft_id.choices = [(a.aircraft_id, f"{a.model} - {a.total_seats} seats") for a in aircrafts]
    form.departure_airport_id.choices = [(a.airport_id, f"{a.name} ({a.IATA_code})") for a in airports]
    form.arrival_airport_id.choices = [(a.airport_id, f"{a.name} ({a.IATA_code})") for a in airports]
    
    if form.validate_on_submit():
        try:
            # Parse duration
            duration_parts = form.duration.data.split(':')
            duration = timedelta(hours=int(duration_parts[0]), minutes=int(duration_parts[1]))
            
            template = FlightTemplate(
                airline_id=form.airline_id.data,
                aircraft_id=form.aircraft_id.data,
                flight_number=form.flight_number.data,
                departure_airport_id=form.departure_airport_id.data,
                arrival_airport_id=form.arrival_airport_id.data,
                duration=duration,
                base_price=form.base_price.data,
                flight_type=form.flight_type.data
            )
            
            db.session.add(template)
            db.session.flush()  # Get the ID
            
            # Create default prices
            price = Price(
                flight_template_id=template.flight_template_id,
                economy_price=form.base_price.data,
                business_price=form.base_price.data * 2.5,
                first_price=form.base_price.data * 4.0
            )
            db.session.add(price)
            
            db.session.commit()
            
            flash('Flight template created successfully!', 'success')
            return redirect(url_for('admin.manage_templates'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the template.', 'danger')
    
    return render_template('admin/add_template.html', form=form)

@bp.route('/templates/<int:template_id>/prices', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_prices(template_id):
    template = FlightTemplate.query.get_or_404(template_id)
    form = PriceForm()
    
    if form.validate_on_submit():
        try:
            if template.prices:
                # Update existing prices
                template.prices.economy_price = form.economy_price.data
                template.prices.business_price = form.business_price.data
                template.prices.first_price = form.first_price.data
            else:
                # Create new prices
                price = Price(
                    flight_template_id=template_id,
                    economy_price=form.economy_price.data,
                    business_price=form.business_price.data,
                    first_price=form.first_price.data
                )
                db.session.add(price)
            
            db.session.commit()
            flash('Prices updated successfully!', 'success')
            return redirect(url_for('admin.manage_templates'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating prices.', 'danger')
    
    # Pre-populate form with current values
    if template.prices:
        form.economy_price.data = template.prices.economy_price
        form.business_price.data = template.prices.business_price
        form.first_price.data = template.prices.first_price
    
    return render_template('admin/manage_prices.html', form=form, template=template)

@bp.route('/discounts')
@login_required
@role_required('admin')
def manage_discounts():
    discounts = Discount.query.join(Flight).order_by(Flight.departure_datetime.desc()).all()
    return render_template('admin/discounts.html', discounts=discounts)

@bp.route('/discounts/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_discount():
    form = DiscountForm()
    
    # Populate flight choices (only active flights)
    flights = Flight.query.filter(Flight.is_active == True).all()
    form.flight_id.choices = [(f.flight_id, f"{f.flight_template.flight_number} - {f.departure_datetime.strftime('%Y-%m-%d %H:%M')}") for f in flights]
    
    if form.validate_on_submit():
        try:
            # Check if discount already exists for this flight
            existing_discount = Discount.query.filter_by(flight_id=form.flight_id.data).first()
            
            if existing_discount:
                existing_discount.discount_percentage = form.discount_percentage.data
            else:
                discount = Discount(
                    flight_id=form.flight_id.data,
                    discount_percentage=form.discount_percentage.data
                )
                db.session.add(discount)
            
            db.session.commit()
            flash('Discount applied successfully!', 'success')
            return redirect(url_for('admin.manage_discounts'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while applying the discount.', 'danger')
    
    return render_template('admin/add_discount.html', form=form)

@bp.route('/discounts/<int:discount_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_discount(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    
    try:
        db.session.delete(discount)
        db.session.commit()
        flash('Discount removed successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while removing the discount.', 'danger')
    
    return redirect(url_for('admin.manage_discounts'))

# @bp.route('/analytics')
# @login_required
# @role_required('admin')
# def analytics():
#     # Revenue analytics
#     total_revenue = db.session.query(func.sum(Invoice.amount)).scalar() or 0
#     total_tickets = db.session.query(func.count(Reservation.reservation_id)).scalar() or 0
#     total_flights = db.session.query(func.count(Flight.flight_id)).scalar() or 0
#     active_flights = db.session.query(func.count(Flight.flight_id)).filter(Flight.is_active == True).scalar() or 0
    
#     # Most popular routes
#     popular_routes = db.session.query(
#         FlightTemplate.departure_airport_id,
#         FlightTemplate.arrival_airport_id,
#         func.count(ReservationSeat.reservation_id).label('booking_count')
#     ).select_from(FlightTemplate).join(Flight, FlightTemplate.flight_template_id == Flight.flight_template_id).join(
#         ReservationSeat, Flight.flight_id == ReservationSeat.flight_id
#     ).group_by(
#         FlightTemplate.departure_airport_id,
#         FlightTemplate.arrival_airport_id
#     ).order_by(func.count(ReservationSeat.reservation_id).desc()).limit(5).all()
    
#     # Monthly revenue
#     monthly_revenue = []
#     for i in range(6):
#         month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
#         month_end = month_start.replace(day=28) + timedelta(days=4)
#         month_end = month_end.replace(day=1) - timedelta(days=1)
        
#         revenue = db.session.query(func.sum(Invoice.amount)).filter(
#             and_(
#                 Invoice.issued_date >= month_start,
#                 Invoice.issued_date <= month_end
#             )
#         ).scalar() or 0
        
#         monthly_revenue.append({
#             'month': month_start.strftime('%B %Y'),
#             'revenue': revenue
#         })
    
#     return render_template('admin/analytics.html',
#                          total_revenue=total_revenue,
#                          total_tickets=total_tickets,
#                          total_flights=total_flights,
#                          active_flights=active_flights,
#                          popular_routes=popular_routes,
#                          monthly_revenue=monthly_revenue)

@bp.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    # Revenue analytics
    total_revenue = db.session.query(func.sum(Invoice.amount)).scalar() or 0
    total_tickets = db.session.query(func.count(Reservation.reservation_id)).scalar() or 0
    total_flights = db.session.query(func.count(Flight.flight_id)).scalar() or 0
    active_flights = db.session.query(func.count(Flight.flight_id)).filter(Flight.is_active == True).scalar() or 0
    
    # Calculate profit as 2% of total revenue
    profit = total_revenue * 0.02
    
    # Most popular routes
    popular_routes = db.session.query(
        FlightTemplate.departure_airport_id,
        FlightTemplate.arrival_airport_id,
        func.count(ReservationSeat.reservation_id).label('booking_count')
    ).select_from(FlightTemplate).join(Flight, FlightTemplate.flight_template_id == Flight.flight_template_id).join(
        ReservationSeat, Flight.flight_id == ReservationSeat.flight_id
    ).group_by(
        FlightTemplate.departure_airport_id,
        FlightTemplate.arrival_airport_id
    ).order_by(func.count(ReservationSeat.reservation_id).desc()).limit(5).all()
    
    # Monthly revenue (last 6 months)
    monthly_revenue = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end.replace(day=1) - timedelta(days=1)
        
        revenue = db.session.query(func.sum(Invoice.amount)).filter(
            and_(
                Invoice.issued_date >= month_start,
                Invoice.issued_date <= month_end
            )
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': revenue
        })
    
    monthly_revenue.reverse()  # so oldest month is first
    
    return render_template('admin/analytics.html',
                         total_revenue=total_revenue,
                         profit=profit,
                         total_tickets=total_tickets,
                         total_flights=total_flights,
                         active_flights=active_flights,
                         popular_routes=popular_routes,
                         monthly_revenue=monthly_revenue)


@bp.route('/users')
@login_required
@role_required('admin')
def manage_users():
    # Get search parameters
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    
    # Build query
    query = User.query
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    users = query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_role(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.user_id == current_user.user_id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.manage_users'))
    
    try:
        user.role = 'admin' if user.role == 'passenger' else 'passenger'
        db.session.commit()
        
        new_role = "admin" if user.role == 'admin' else "passenger"
        flash(f'User role changed to {new_role} successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while changing user role.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@bp.route('/users/<int:user_id>/details')
@login_required
@role_required('admin')
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's booking history
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.reservation_date.desc()).all()
    
    booking_details = []
    for reservation in reservations:
        reservation_seats = ReservationSeat.query.filter_by(reservation_id=reservation.reservation_id).all()
        for reservation_seat in reservation_seats:
            passenger = Passenger.query.get(reservation_seat.passenger_id)
            seat = Seat.query.get(reservation_seat.seat_id)
            flight = Flight.query.get(reservation_seat.flight_id)
            booking_details.append({
                'reservation': reservation,
                'flight': flight,
                'passenger': passenger,
                'seat': seat
            })

    
    return render_template('admin/user_details.html', user=user, booking_details=booking_details)
