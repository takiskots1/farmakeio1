import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email, ValidationError
class LoginForm(FlaskForm):
    username=StringField('Όνομα χρήστη',validators=[DataRequired()])
    password=PasswordField('Κωδικός',validators=[DataRequired()])
    submit=SubmitField('Σύνδεση')
class ClientForm(FlaskForm):
    full_name=StringField('Ονοματεπώνυμο',validators=[DataRequired(),Length(max=150)])
    amka=StringField('ΑΜΚΑ (11 ψηφία)',validators=[Optional(),Length(min=11,max=11)])
    phone=StringField('Κινητό',validators=[Optional(),Length(max=30)])
    email=StringField('Email',validators=[Optional(),Email()])
    sms_consent=BooleanField('Συγκατάθεση για SMS υπενθυμίσεις')
    email_consent=BooleanField('Συγκατάθεση για email υπενθυμίσεις')
    username=StringField('Username πελάτη (προαιρετικό)',validators=[Optional(),Length(max=100)])
    password=PasswordField('Αρχικός κωδικός (για νέο login)')
    submit=SubmitField('Αποθήκευση')
    def validate_amka(self,field):
        if field.data and not re.fullmatch(r'\d{11}',field.data): raise ValidationError('Το ΑΜΚΑ πρέπει να έχει 11 ψηφία.')
class PrescriptionForm(FlaskForm):
    title=StringField('Περιγραφή',validators=[DataRequired(),Length(max=150)])
    opens_on=DateField('Ημερομηνία ανοίγματος',format='%Y-%m-%d',validators=[DataRequired()])
    notes=TextAreaField('Εσωτερικές σημειώσεις')
    active=BooleanField('Ενεργή',default=True)
    submit=SubmitField('Αποθήκευση')
class MessageForm(FlaskForm):
    body=TextAreaField('Μήνυμα',validators=[DataRequired(),Length(min=1,max=3000)])
    portal=BooleanField('Στην προσωπική καρτέλα',default=True)
    sms=BooleanField('SMS μέσω SMS.to')
    email=BooleanField('Email μέσω SMTP')
    push=BooleanField('Push notification στη συσκευή')
    submit=SubmitField('Καταχώριση και αποστολή')

class ClientReplyForm(FlaskForm):
    body=TextAreaField('Το μήνυμά σας',validators=[DataRequired(),Length(min=2,max=2000)])
    submit=SubmitField('Αποστολή στο φαρμακείο')

from wtforms import SelectField, TimeField
from wtforms.validators import NumberRange
from services.notifications import local_today

class MedicationReminderForm(FlaskForm):
    medication_name = StringField('Όνομα φαρμάκου', validators=[DataRequired(), Length(max=160)])
    instructions = StringField('Οδηγίες όπως έχουν δοθεί από τον επαγγελματία υγείας (προαιρετικό)', validators=[Optional(), Length(max=240)])
    remind_at = TimeField('Ώρα υπενθύμισης (Ελλάδα)', format='%H:%M', validators=[DataRequired()])
    start_date = DateField('Έναρξη', format='%Y-%m-%d', validators=[DataRequired()], default=local_today)
    end_date = DateField('Λήξη (προαιρετικό)', format='%Y-%m-%d', validators=[Optional()])
    enabled = BooleanField('Ενεργή υπενθύμιση', default=True)
    channel_portal = BooleanField('Μήνυμα στην καρτέλα', default=True)
    channel_sms = BooleanField('SMS.to')
    channel_email = BooleanField('Email')
    channel_push = BooleanField('Push notification')
    submit = SubmitField('Αποθήκευση υπενθύμισης')

    def validate_end_date(self, field):
        if field.data and self.start_date.data and field.data < self.start_date.data:
            raise ValidationError('Η λήξη πρέπει να είναι μετά την έναρξη.')

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if not any((self.channel_portal.data, self.channel_sms.data,
                    self.channel_email.data, self.channel_push.data)):
            self.channel_portal.errors.append('Επίλεξε τουλάχιστον έναν τρόπο ειδοποίησης.')
            return False
        return ok

_BP_CHOICES = [(0, '— Επιλέξτε —')] + [(i, f'{i/10:g}') for i in range(50, 251, 5)]

class BloodPressureForm(FlaskForm):
    measured_on = DateField('Ημερομηνία μέτρησης', format='%Y-%m-%d', validators=[DataRequired()], default=local_today)
    bp_high_mmhg = SelectField('Μεγάλη (συστολική)', choices=_BP_CHOICES, coerce=int, validators=[DataRequired()])
    bp_low_mmhg = SelectField('Μικρή (διαστολική)', choices=_BP_CHOICES, coerce=int, validators=[DataRequired()])
    submit = SubmitField('Καταχώριση πίεσης')

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if self.measured_on.data and self.measured_on.data > local_today():
            self.measured_on.errors.append('Δεν καταχωρούμε μετρήσεις για μελλοντική ημέρα.')
            ok = False
        if (self.bp_high_mmhg.data is not None and self.bp_low_mmhg.data is not None and
                self.bp_high_mmhg.data <= self.bp_low_mmhg.data):
            self.bp_high_mmhg.errors.append('Η μεγάλη πίεση πρέπει να είναι μεγαλύτερη από τη μικρή.')
            ok = False
        return ok

class GlucoseForm(FlaskForm):
    measured_on = DateField('Ημερομηνία μέτρησης', format='%Y-%m-%d', validators=[DataRequired()], default=local_today)
    glucose_mgdl = SelectField('Σάκχαρο (mg/dL)', choices=[(0, '— Επιλέξτε —')] + [(i, str(i)) for i in range(60, 501)],
                                coerce=int, validators=[DataRequired()])
    submit = SubmitField('Καταχώριση σακχάρου')

    def validate(self, extra_validators=None):
        ok = super().validate(extra_validators=extra_validators)
        if self.measured_on.data and self.measured_on.data > local_today():
            self.measured_on.errors.append('Δεν καταχωρούμε μετρήσεις για μελλοντική ημέρα.')
            ok = False
        return ok

class MeasurementExportForm(FlaskForm):
    recipient = StringField('Email παραλήπτη', validators=[DataRequired(), Email(), Length(max=255)])
    confirm = BooleanField('Επιβεβαιώνω ότι θέλω αποστολή προσωπικών δεδομένων υγείας σε αυτή τη διεύθυνση',
                           validators=[DataRequired(message='Απαιτείται επιβεβαίωση παραλήπτη.')])
    submit = SubmitField('Αποστολή μετρήσεων με email')
