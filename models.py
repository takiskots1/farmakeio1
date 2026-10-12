from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db

def now(): return datetime.now(timezone.utc)
class User(UserMixin, db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),unique=True,nullable=False,index=True)
    password_hash=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(10),nullable=False,default='client')
    client_id=db.Column(db.Integer,db.ForeignKey('clients.id'),unique=True,nullable=True)
class Client(db.Model):
    __tablename__='clients'
    id=db.Column(db.Integer,primary_key=True)
    full_name=db.Column(db.String(150),nullable=False)
    amka=db.Column(db.String(11),unique=True,index=True,nullable=True)
    phone=db.Column(db.String(30),nullable=True)
    email=db.Column(db.String(255),nullable=True)
    sms_consent=db.Column(db.Boolean,nullable=False,default=False)
    email_consent=db.Column(db.Boolean,nullable=False,default=False)
    prescriptions=db.relationship('Prescription',backref='client',lazy=True)
class Prescription(db.Model):
    __tablename__='prescriptions'
    id=db.Column(db.Integer,primary_key=True)
    client_id=db.Column(db.Integer,db.ForeignKey('clients.id'),nullable=False,index=True)
    title=db.Column(db.String(150),nullable=False,default='Μηνιαία συνταγή')
    opens_on=db.Column(db.Date,nullable=False,index=True)
    notes=db.Column(db.Text,nullable=True)
    active=db.Column(db.Boolean,nullable=False,default=True)
class Message(db.Model):
    __tablename__='messages'
    id=db.Column(db.Integer,primary_key=True)
    client_id=db.Column(db.Integer,db.ForeignKey('clients.id'),nullable=False)
    body=db.Column(db.Text,nullable=False)
    direction=db.Column(db.String(20),nullable=False,default='admin_to_client',server_default='admin_to_client',index=True)
    read_at=db.Column(db.DateTime(timezone=True),nullable=True)
    portal_visible=db.Column(db.Boolean,nullable=False,default=True,server_default='true')
    created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)
class NotificationLog(db.Model):
    __tablename__='notification_logs'
    id=db.Column(db.Integer,primary_key=True)
    prescription_id=db.Column(db.Integer,db.ForeignKey('prescriptions.id'),nullable=False)
    channel=db.Column(db.String(10),nullable=False)
    event_date=db.Column(db.Date,nullable=False)
    status=db.Column(db.String(20),nullable=False)
    provider_id=db.Column(db.String(100))
    error=db.Column(db.String(300))
    created_at=db.Column(db.DateTime(timezone=True),default=now,nullable=False)
    __table_args__=(db.UniqueConstraint('prescription_id','channel','event_date',name='uq_notification_day'),)

class MessageDelivery(db.Model):
    __tablename__='message_deliveries'
    id=db.Column(db.Integer,primary_key=True)
    message_id=db.Column(db.Integer,db.ForeignKey('messages.id',ondelete='CASCADE'),nullable=False,index=True)
    channel=db.Column(db.String(12),nullable=False)
    status=db.Column(db.String(20),nullable=False,default='processing')
    provider_id=db.Column(db.String(120),nullable=True)
    error=db.Column(db.String(300),nullable=True)
    created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=now)
    message=db.relationship('Message',backref=db.backref('deliveries',lazy=True,cascade='all,delete-orphan'))
    __table_args__=(db.UniqueConstraint('message_id','channel',name='uq_message_delivery_channel'),)

class PushSubscription(db.Model):
    __tablename__='push_subscriptions'
    id=db.Column(db.Integer,primary_key=True)
    client_id=db.Column(db.Integer,db.ForeignKey('clients.id',ondelete='CASCADE'),nullable=False,index=True)
    endpoint=db.Column(db.Text,nullable=False,unique=True)
    p256dh=db.Column(db.Text,nullable=False)
    auth=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime(timezone=True),nullable=False,default=now)

class MedicationReminder(db.Model):
    __tablename__ = 'medication_reminders'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    medication_name = db.Column(db.String(160), nullable=False)
    instructions = db.Column(db.String(240), nullable=True)
    remind_at = db.Column(db.Time, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    channel_portal = db.Column(db.Boolean, nullable=False, default=True)
    channel_sms = db.Column(db.Boolean, nullable=False, default=False)
    channel_email = db.Column(db.Boolean, nullable=False, default=False)
    channel_push = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    client = db.relationship('Client', backref=db.backref('medication_reminders', lazy=True))

class MedicationReminderDelivery(db.Model):
    __tablename__ = 'medication_reminder_deliveries'
    id = db.Column(db.Integer, primary_key=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey('medication_reminders.id', ondelete='CASCADE'), nullable=False, index=True)
    delivery_date = db.Column(db.Date, nullable=False)
    channel = db.Column(db.String(12), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='processing')
    provider_id = db.Column(db.String(120), nullable=True)
    error = db.Column(db.String(300), nullable=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    reminder = db.relationship('MedicationReminder', backref=db.backref('delivery_logs', lazy=True))
    __table_args__ = (db.UniqueConstraint('reminder_id', 'delivery_date', 'channel',
                                         name='uq_med_reminder_delivery'),)

class HealthMeasurement(db.Model):
    __tablename__ = 'health_measurements'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    measured_on = db.Column(db.Date, nullable=False, index=True)
    kind = db.Column(db.String(12), nullable=False)
    bp_high_mmhg = db.Column(db.Integer, nullable=True)
    bp_low_mmhg = db.Column(db.Integer, nullable=True)
    glucose_mgdl = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    client = db.relationship('Client', backref=db.backref('health_measurements', lazy=True))

    @property
    def high_display(self):
        return f'{self.bp_high_mmhg / 10:g}' if self.bp_high_mmhg is not None else '—'

    @property
    def low_display(self):
        return f'{self.bp_low_mmhg / 10:g}' if self.bp_low_mmhg is not None else '—'
