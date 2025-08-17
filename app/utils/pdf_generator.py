# utils/pdf_generator.py
from app.models import Seat  # Import at the top of pdf_generator.py
from fpdf import FPDF
import qrcode
import io
import random
import string


def generate_ticket_pdf(reservation, passenger_seat_pairs, flight):
    # Generate a random QR code string
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(f"QR-CODE-{random_code}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code to BytesIO
    qr_bytes = io.BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)

    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Flight Ticket", ln=True, align='C')
    pdf.ln(5)

    # Reservation info
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Ticket Number: TKT-{reservation.reservation_id:06d}", ln=True)
    pdf.cell(0, 10, f"Airline: {flight.flight_template.airline.name}", ln=True)
    pdf.cell(0, 10, f"Flight Number: {flight.flight_template.flight_number}", ln=True)
    pdf.cell(
        0, 10,
        f"Route: {flight.flight_template.departure_airport.name} ({flight.flight_template.departure_airport.IATA_code}) "
        f"-> {flight.flight_template.arrival_airport.name} ({flight.flight_template.arrival_airport.IATA_code})",
        ln=True
    )
    pdf.cell(0, 10, f"Departure: {flight.departure_datetime.strftime('%B %d, %Y %I:%M %p')}", ln=True)
    pdf.cell(0, 10, f"Arrival: {flight.arrival_datetime.strftime('%B %d, %Y %I:%M %p')}", ln=True)
    pdf.ln(5)

    # Passenger & seat info
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Passengers & Seat Assignments", ln=True)
    pdf.set_font("Helvetica", '', 12)
    for idx, pair in enumerate(passenger_seat_pairs, start=1):
        pdf.cell(0, 8, f"{idx}. {pair['passenger'].first_name} {pair['passenger'].last_name}", ln=True)
        pdf.cell(0, 8, f"   Contact: {pair['passenger'].contact_number}", ln=True)
        pdf.cell(0, 8, f"   Seat: {pair['seat'].seat_number} | Class: {pair['seat'].class_.value} | Position: {pair['seat'].position.value}", ln=True)
        pdf.ln(3)

    # Payment details
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Payment Details", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"Amount Paid: ${reservation.total_price:.2f}", ln=True)
    pdf.cell(0, 8, f"Payment Method: {reservation.payment_method}", ln=True)
    pdf.cell(0, 8, f"Status: {reservation.status.value}", ln=True)
    pdf.ln(5)

    # QR Code (directly from BytesIO)
    pdf.image(qr_bytes, x=80, w=50)

    # Instructions
    pdf.ln(55)
    pdf.set_font("Helvetica", 'I', 11)
    pdf.multi_cell(
        0, 8,
        "Please print your physical ticket at the airport using the above QR code. "
        "This QR code contains your booking reference for verification. "
        "Keep this ticket with you at all times.",
        align='C'
    )

    # Return PDF as bytes for download
    return pdf.output(dest='S')


def generate_invoice_pdf(reservation, reservation_seats, flight, user_info):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Invoice", ln=True, align='C')
    pdf.ln(10)

    # Reservation info
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 10, f"Invoice Number: INV-{reservation.reservation_id:06d}", ln=True)
    pdf.cell(0, 10, f"Reservation Date: {reservation.reservation_date.strftime('%B %d, %Y')}", ln=True)
    pdf.ln(5)

    # User info instead of passenger info
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "User Information", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"Name: {user_info['name']}", ln=True)
    pdf.cell(0, 8, f"Email: {user_info['email']}", ln=True)
    pdf.ln(5)

    # Flight info
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Flight Details", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"Flight Number: {flight.flight_template.flight_number}", ln=True)
    pdf.cell(0, 8, f"Airline: {flight.flight_template.airline.name}", ln=True)
    pdf.cell(0, 8, f"Route: {flight.flight_template.departure_airport.IATA_code} -> {flight.flight_template.arrival_airport.IATA_code}", ln=True)
    pdf.cell(0, 8, f"Departure: {flight.departure_datetime.strftime('%B %d, %Y %I:%M %p')}", ln=True)
    pdf.cell(0, 8, f"Arrival: {flight.arrival_datetime.strftime('%B %d, %Y %I:%M %p')}", ln=True)
    pdf.ln(5)

    # Seats info table header
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Seats Reserved", ln=True)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(40, 8, "Seat Number", border=1)
    pdf.cell(50, 8, "Class", border=1)
    pdf.cell(50, 8, "Position", border=1, ln=True)

    # Loop over reservation seats and fetch seat details manually
    pdf.set_font("Helvetica", '', 12)
    for rs in reservation_seats:
        seat = Seat.query.get(rs.seat_id)
        pdf.cell(40, 8, seat.seat_number, border=1)
        pdf.cell(50, 8, seat.class_.value, border=1)
        pdf.cell(50, 8, seat.position.value, border=1, ln=True)

    pdf.ln(5)

    # Payment info
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "Payment Information", ln=True)
    pdf.set_font("Helvetica", '', 12)
    pdf.cell(0, 8, f"Amount Paid: ${reservation.total_price:.2f}", ln=True)
    pdf.cell(0, 8, f"Payment Method: {reservation.payment_method}", ln=True)
    pdf.cell(0, 8, f"Status: {reservation.status.value}", ln=True)
    pdf.ln(5)

    # Footer / note
    pdf.set_font("Helvetica", 'I', 10)
    pdf.multi_cell(0, 10, "Thank you for booking with us. Please keep this invoice for your records.")

    return pdf.output(dest='S')
