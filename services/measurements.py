"""Patient-controlled export of recorded measurements via the configured SMTP."""
import csv
import io
import os
import smtplib
import ssl
from email.message import EmailMessage

from models import HealthMeasurement


def measurement_csv(client_id):
    """Return bytes with BOM for Excel, only the authenticated client's measurements."""
    rows = (HealthMeasurement.query.filter_by(client_id=client_id)
            .order_by(HealthMeasurement.measured_on.desc(), HealthMeasurement.id.desc())
            .limit(5000).all())
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Ημερομηνία', 'Τύπος', 'Μεγάλη πίεση (mmHg)',
                     'Μικρή πίεση (mmHg)', 'Σάκχαρο (mg/dL)'])
    for item in rows:
        writer.writerow([item.measured_on.strftime('%Y-%m-%d'),
                         'Αρτηριακή πίεση' if item.kind == 'bp' else 'Σάκχαρο',
                         item.bp_high_mmhg if item.kind == 'bp' else '',
                         item.bp_low_mmhg if item.kind == 'bp' else '',
                         item.glucose_mgdl if item.kind == 'glucose' else ''])
    return ('\ufeff' + output.getvalue()).encode('utf-8'), len(rows)


def send_measurements_email(recipient, csv_data):
    """Send health data only on an authenticated client's explicit request."""
    host = os.getenv('SMTP_HOST')
    sender = os.getenv('SMTP_FROM')
    if os.getenv('EMAIL_ENABLED', '').strip().lower() != 'true' or not host or not sender:
        raise RuntimeError('Η αποστολή email δεν έχει ενεργοποιηθεί.')
    msg = EmailMessage()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = 'CHRYSPHARMACY | Προσωπικό αρχείο μετρήσεων'
    msg.set_content('Συνημμένο αρχείο μετρήσεων, κατόπιν αιτήματός σας. '
                    'Το μήνυμα περιλαμβάνει προσωπικά δεδομένα υγείας. Φυλάξτε το με ασφάλεια.')
    msg.add_attachment(csv_data, maintype='text', subtype='csv', filename='measurements.csv')
    port = int(os.getenv('SMTP_PORT', '587'))
    if port != 465 and os.getenv('SMTP_STARTTLS', 'true').strip().lower() != 'true':
        raise RuntimeError('Απαιτείται κρυπτογραφημένη σύνδεση SMTP (STARTTLS ή SSL).')
    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, timeout=20, context=ssl.create_default_context())
    else:
        smtp = smtplib.SMTP(host, port, timeout=20)
    with smtp as server:
        if port != 465 and os.getenv('SMTP_STARTTLS', 'true').strip().lower() == 'true':
            server.starttls(context=ssl.create_default_context())
        if os.getenv('SMTP_USER'):
            server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD', ''))
        server.send_message(msg)
