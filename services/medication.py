"""Daily medication reminders, evaluated in Europe/Athens.

Never include a medication name, dosage, patient ID, or AMKA in SMS/email/push.
Records a unique (reminder, date, channel) claim BEFORE contacting a provider,
so the minute-by-minute cron task cannot double-send on repeated invocations.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from extensions import db
from models import MedicationReminder, MedicationReminderDelivery, Message, User
from services.messaging import channel_blockers, send_push
from services.notifications import send_email, send_sms

ATHENS = ZoneInfo('Europe/Athens')
EXTERNAL_BODY = ('CHRYSPHARMACY: Έχετε προγραμματισμένη υπενθύμιση λήψης φαρμάκου. '
                 'Δείτε το πρόγραμμα στην προσωπική σας καρτέλα.')


def local_now():
    return datetime.now(ATHENS)


def reminder_channels(reminder):
    return [channel for channel in ('portal', 'sms', 'email', 'push')
            if getattr(reminder, 'channel_' + channel, False)]


def reminder_blockers(reminder):
    blockers = {}
    for channel in reminder_channels(reminder):
        blockers[channel] = channel_blockers(reminder.client, channel)
        if channel == 'portal' and not User.query.filter_by(client_id=reminder.client_id, role='client').first():
            blockers[channel] = ['Δεν υπάρχει λογαριασμός σύνδεσης πελάτη']
    return blockers


def reminder_is_due(reminder, now, grace_minutes=10):
    if not reminder.enabled:
        return False
    today = now.date()
    if reminder.start_date > today or (reminder.end_date and reminder.end_date < today):
        return False
    # Compare on local wall-clock time: one dispatch per Greek calendar day,
    # including during the repeated hour at the DST transition.
    current_minute = now.hour * 60 + now.minute
    scheduled_minute = reminder.remind_at.hour * 60 + reminder.remind_at.minute
    return 0 <= current_minute - scheduled_minute < grace_minutes


def process_due_reminders(now=None, dry_run=False):
    now = now or local_now()
    today = now.date()
    stats = dict(due=0, claimed=0, queued=0, saved=0, sent=0, failed=0,
                 blocked=0, already_attempted=0)
    reminders = (MedicationReminder.query.filter_by(enabled=True)
                 .filter(MedicationReminder.start_date <= today)
                 .filter((MedicationReminder.end_date.is_(None)) |
                         (MedicationReminder.end_date >= today)).all())
    for reminder in reminders:
        if not reminder_is_due(reminder, now):
            continue
        stats['due'] += 1
        blocked = reminder_blockers(reminder)
        for channel in reminder_channels(reminder):
            existing = MedicationReminderDelivery.query.filter_by(
                reminder_id=reminder.id, delivery_date=today, channel=channel).first()
            if existing:
                stats['already_attempted'] += 1
                continue
            if dry_run:
                stats['blocked' if blocked.get(channel) else 'claimed'] += 1
                continue
            # Record a claim to avoid repeated external sends. Failed attempts are
            # not retried automatically because the provider may have accepted them.
            log = MedicationReminderDelivery(reminder_id=reminder.id,
                                             delivery_date=today, channel=channel,
                                             status='processing')
            db.session.add(log)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                stats['already_attempted'] += 1
                continue
            stats['claimed'] += 1
            if blocked.get(channel):
                log.status = 'blocked'
                # Generic metadata: no contact address, phone, drug name, or API key.
                log.error = 'Απαιτείται έλεγχος ρυθμίσεων ή συναίνεσης.'
                stats['blocked'] += 1
                db.session.commit()
                continue
            try:
                if channel == 'portal':
                    body = 'Υπενθύμιση λήψης: ' + reminder.medication_name
                    if reminder.instructions:
                        body += ' — ' + reminder.instructions
                    message = Message(client_id=reminder.client_id, body=body,
                                      direction='admin_to_client', portal_visible=True)
                    db.session.add(message)
                    db.session.flush()
                    log.message_id = message.id
                    log.status = 'saved'
                    stats['saved'] += 1
                elif channel == 'sms':
                    provider_id = send_sms(reminder.client.phone, EXTERNAL_BODY)
                    log.provider_id = str(provider_id or '')[:120]
                    log.status = 'queued'
                    stats['queued'] += 1
                elif channel == 'email':
                    send_email(reminder.client.email, 'CHRYSPHARMACY · Υπενθύμιση', EXTERNAL_BODY)
                    log.status = 'sent'
                    stats['sent'] += 1
                elif channel == 'push':
                    log.provider_id = str(send_push(
                        reminder.client, body='Ώρα για την προγραμματισμένη σας υπενθύμιση. Δείτε την καρτέλα σας.',
                        url='/client/medications'))[:120]
                    log.status = 'queued'
                    stats['queued'] += 1
                else:
                    raise RuntimeError('Unknown notification channel')
            except Exception:
                log.status = 'failed'
                log.error = 'Η αποστολή απέτυχε. Ελέγξτε τις ρυθμίσεις και τον πάροχο.'
                stats['failed'] += 1
            db.session.commit()
    return stats
