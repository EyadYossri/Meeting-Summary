import smtplib
from email.mime.text import MIMEText

def send_email(sender_email, sender_password, receiver_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15, source_address=('0.0.0.0', 0)) as server:
            
            server.set_debuglevel(1) 
            
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
    except Exception as e:
        raise Exception(f"SMTP Error: {str(e)}")
