import os
import logging
import smtplib
from twilio.rest import Client

logger = logging.getLogger(__name__)

def _require_env(*vars_list):
    missing = [v for v in vars_list if not os.environ.get(v)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

def send_advanced_alert(subject, message):
    send_email_alert(subject, message)
    send_whatsapp_alert(message)

def send_alert(alert_type, details):
    send_advanced_alert(alert_type, details)

def send_email_alert(subject, message):
    _require_env("EMAIL_USER", "EMAIL_PASS", "EMAIL_HOST", "EMAIL_PORT", "ALERT_RECIPIENT_EMAIL")
    sender_email = os.environ["EMAIL_USER"]
    receiver_email = os.environ["ALERT_RECIPIENT_EMAIL"]
    password = os.environ["EMAIL_PASS"]
    host = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("EMAIL_PORT", 465))
    try:
        server = smtplib.SMTP_SSL(host, port)
        server.login(sender_email, password)
        message = f'Subject: {subject}\n\n{message}'
        server.sendmail(sender_email, receiver_email, message)
        server.quit()
    except Exception as e:
        logger.error(f"Error sending email: {e}")

def send_whatsapp_alert(message):
    _require_env("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM", "WHATSAPP_TO")
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]
    from_ = os.environ["TWILIO_WHATSAPP_FROM"]
    to = os.environ["WHATSAPP_TO"]
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=message,
        from_=from_,
        to=to
    )
    logger.info(f"WhatsApp message sent: {message.sid}")
