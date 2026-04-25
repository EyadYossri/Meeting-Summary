import smtplib
import socket
from email.mime.text import MIMEText

original_getaddrinfo = socket.getaddrinfo

def force_ipv4_getaddrinfo(*args, **kwargs):
    responses = original_getaddrinfo(*args, **kwargs)
    return [res for res in responses if res[0] == socket.AF_INET]

socket.getaddrinfo = force_ipv4_getaddrinfo

def send_email(sender_email, sender_password, receiver_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as server:
            
            server.set_debuglevel(1) 
            
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
    except Exception as e:
        raise Exception(f"SMTP Error: {str(e)}")
