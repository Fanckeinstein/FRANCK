import os
import random
import smtplib
from email.message import EmailMessage

try:
    import requests
except ImportError:
    requests = None

try:
    from twilio.rest import Client
except ImportError:
    Client = None

DEV_MODE = os.getenv('VERIF_DEV_MODE', '1') == '1'


def generate_code(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def send_email(to_email, subject, body):
    """Send email via SMTP if configured, otherwise log to console (dev mode)."""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')
    smtp_from = os.getenv('SMTP_FROM', 'noreply@unissonslamain.local')

    if not smtp_host or DEV_MODE:
        print(f"[DEV EMAIL] To={to_email} Subject={subject} Body={body}")
        return True

    msg = EmailMessage()
    msg['From'] = smtp_from
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as s:
            s.starttls()
            if smtp_user and smtp_pass:
                s.login(smtp_user, smtp_pass)
            s.send_message(msg)
        return True
    except Exception as e:
        print('send_email error:', e)
        return False


def send_whatsapp(to_number, body):
    """Send WhatsApp message via Twilio API if configured, otherwise log to console (dev mode)."""
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_whatsapp = os.getenv('TWILIO_WHATSAPP_FROM')

    if not account_sid or not auth_token or not from_whatsapp or DEV_MODE or not Client:
        print(f"[DEV WHATSAPP] To={to_number} Body={body}")
        return True

    try:
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            from_=from_whatsapp,
            to=f'whatsapp:{to_number.lstrip("+")}' if not to_number.startswith('whatsapp:') else to_number,
            body=body,
        )
        return True
    except Exception as e:
        print('send_whatsapp error:', e)
        return False
