from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, FloatField, BooleanField, TextAreaField, RadioField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from wtforms import SelectField
from datetime import datetime, date
from app.models import SeatClass, TripType, FlightType, SeatPosition

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

class FlightSearchForm(FlaskForm):
    # Location Filters
    departure_country = SelectField('Departure Country', coerce=str, validators=[DataRequired()])
    departure_city = SelectField('Departure City', coerce=str, validators=[Optional()])
    departure_airport = SelectField('Departure Airport', coerce=int, validators=[Optional()])
    
    arrival_country = SelectField('Arrival Country', coerce=str, validators=[DataRequired()])
    arrival_city = SelectField('Arrival City', coerce=str, validators=[Optional()])
    arrival_airport = SelectField('Arrival Airport', coerce=int, validators=[Optional()])
    
    # Trip Details
    trip_type = RadioField('Trip Type', choices=[
        (TripType.One_way.value, 'One Way'),
        (TripType.Round_trip.value, 'Round Trip')
    ], validators=[DataRequired()])
    
    departure_date = DateField('Departure Date', validators=[DataRequired()])
    return_date = DateField('Return Date', validators=[Optional()])
    passengers = IntegerField('Number of Passengers', validators=[DataRequired(), NumberRange(min=1, max=9)])
    
    # Class & Preferences
    seat_class = RadioField('Class', choices=[
        (SeatClass.Economy.value, 'Economy'),
        (SeatClass.Business.value, 'Business'),
        (SeatClass.First.value, 'First Class')
    ], validators=[DataRequired()])
    
    seat_preference = SelectField('Seat Preference (Economy only)', choices=[
        ('', 'No Preference'),
        (SeatPosition.Window.value, 'Window'),
        (SeatPosition.Aisle.value, 'Aisle'),
        (SeatPosition.Middle.value, 'Middle')
    ], validators=[Optional()])
    
    flight_type = RadioField('Flight Type', choices=[
        (FlightType.Domestic.value, 'Domestic'),
        (FlightType.International.value, 'International')
    ], validators=[DataRequired()])
    
    preferred_airline = SelectField('Preferred Airline', coerce=int, validators=[Optional()])
    
    # Time & Price Options
    departure_time_range = SelectField('Departure Time Range', choices=[
        ('', 'Any Time'),
        ('morning', 'Morning (6:00 AM - 12:00 PM)'),
        ('afternoon', 'Afternoon (12:00 PM - 6:00 PM)'),
        ('evening', 'Evening (6:00 PM - 12:00 AM)'),
        ('night', 'Night (12:00 AM - 6:00 AM)')
    ], validators=[Optional()])
    
    return_time_range = SelectField('Return Time Range', choices=[
        ('', 'Any Time'),
        ('morning', 'Morning (6:00 AM - 12:00 PM)'),
        ('afternoon', 'Afternoon (12:00 PM - 6:00 PM)'),
        ('evening', 'Evening (6:00 PM - 12:00 AM)'),
        ('night', 'Night (12:00 AM - 6:00 AM)')
    ], validators=[Optional()])
    
    max_budget = FloatField('Max Budget (PKR)', validators=[Optional(), NumberRange(min=0)])
    show_discounted_only = BooleanField('Show Only Discounted Flights')
    
    sort_by = SelectField('Sort By', choices=[
        ('price', 'Price (Low to High)'),
        ('price_desc', 'Price (High to Low)'),
        ('duration', 'Duration (Shortest)'),
        ('airline', 'Airline Name'),
        ('departure_time', 'Departure Time')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Search Flights')

    def __init__(self, *args, **kwargs):
        super(FlightSearchForm, self).__init__(*args, **kwargs)
        # Initialize optional fields with None
        if not hasattr(self, 'departure_airport') or self.departure_airport.data is None:
            self.departure_airport.data = None
        if not hasattr(self, 'arrival_airport') or self.arrival_airport.data is None:
            self.arrival_airport.data = None
        if not hasattr(self, 'preferred_airline') or self.preferred_airline.data is None:
            self.preferred_airline.data = None
        if not hasattr(self, 'max_budget') or self.max_budget.data is None:
            self.max_budget.data = None

    def validate_departure_airport(self, field):
        if field.data == '' or field.data == 'None':
            field.data = None

    def validate_arrival_airport(self, field):
        if field.data == '' or field.data == 'None':
            field.data = None

    def validate_preferred_airline(self, field):
        if field.data == '' or field.data == 'None':
            field.data = None

    def validate_max_budget(self, field):
        if field.data == '' or field.data == 'None':
            field.data = None

class PassengerInfoForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    passport_no = StringField('Passport Number', validators=[DataRequired()])
    contact_number = StringField('Contact Number', validators=[DataRequired()])

class PaymentForm(FlaskForm):
    card_number = StringField('Card Number', validators=[DataRequired(), Length(min=13, max=19)])
    card_holder = StringField('Card Holder Name', validators=[DataRequired()])
    expiry_month = SelectField('Expiry Month', choices=[
        ('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'),
        ('05', '05'), ('06', '06'), ('07', '07'), ('08', '08'),
        ('09', '09'), ('10', '10'), ('11', '11'), ('12', '12')
    ], validators=[DataRequired()])
    expiry_year = SelectField('Expiry Year', choices=[
        ('2025', '2025'), ('2026', '2026'), ('2027', '2027'),
        ('2028', '2028'), ('2029', '2029'), ('2030', '2030')
    ], validators=[DataRequired()])
    cvv = StringField('CVV', validators=[DataRequired(), Length(min=3, max=4)])
    submit = SubmitField('Pay Now')

class FlightTemplateForm(FlaskForm):
    airline_id = SelectField('Airline', coerce=int, validators=[DataRequired()])
    aircraft_id = SelectField('Aircraft', coerce=int, validators=[DataRequired()])
    flight_number = StringField('Flight Number', validators=[DataRequired()])
    departure_airport_id = SelectField('Departure Airport', coerce=int, validators=[DataRequired()])
    arrival_airport_id = SelectField('Arrival Airport', coerce=int, validators=[DataRequired()])
    duration = StringField('Duration (HH:MM)', validators=[DataRequired()])
    base_price = FloatField('Base Price', validators=[DataRequired(), NumberRange(min=0)])
    flight_type = SelectField('Flight Type', choices=[
        (FlightType.Domestic.value, 'Domestic'),
        (FlightType.International.value, 'International')
    ], validators=[DataRequired()])
    submit = SubmitField('Create Flight Template')

class FlightForm(FlaskForm):
    flight_template_id = SelectField('Flight Template', coerce=int, validators=[DataRequired()])
    departure_datetime = StringField('Departure Date & Time', validators=[DataRequired()])
    arrival_datetime = StringField('Arrival Date & Time', validators=[DataRequired()])
    timezone_diff = IntegerField('Timezone Difference (hours)', validators=[DataRequired()])
    submit = SubmitField('Schedule Flight')

class DiscountForm(FlaskForm):
    flight_id = SelectField('Flight', coerce=int, validators=[DataRequired()])
    discount_percentage = FloatField('Discount Percentage', validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Apply Discount')

class PriceForm(FlaskForm):
    economy_price = FloatField('Economy Price', validators=[DataRequired(), NumberRange(min=0)])
    business_price = FloatField('Business Price', validators=[DataRequired(), NumberRange(min=0)])
    first_price = FloatField('First Class Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Set Prices')