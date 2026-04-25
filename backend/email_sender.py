import os
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_email(receiver_email, subject, body):
    try:
        
        params = {
            "from": "AI Meeting Assistant <onboarding@resend.dev>",
            "to": [receiver_email],
            "subject": subject,
            "text": body,
        }

        email_response = resend.Emails.send(params)
        
        print(f"Email sent successfully! ID: {email_response.get('id')}")

    except Exception as e:
        raise Exception(f"Email API Error: {str(e)}")
