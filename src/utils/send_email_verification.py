from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import smtplib
import os

load_dotenv()

class SendEmailVerification:
    def __init__(self) -> None:
        self.sender_email:str = os.getenv('sender_email')
        self.sender_password:str = os.getenv('sender_password')
        
    def send_verification_email(self, recipient_email: str, verification_code: str) -> None:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Lectify Verification Code"
        message["From"] = self.sender_email
        message["To"] = recipient_email

        text = f"""Hello,
You're almost there! To complete your account creation or password recovery, please use the verification code below:
        
        {verification_code}
        
This code is valid for 10 minutes.

If you are not in the process of creating an account or recovering your password, please ignore this email.

Regards,
Lectify
"""
        
        part = MIMEText(text, "plain")
        message.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipient_email, message.as_string())