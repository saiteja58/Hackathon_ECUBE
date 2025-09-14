import smtplib
from email.message import EmailMessage

# ---------- CONFIG ----------
EMAIL_ADDRESS = "saitejabairoju1@gmail.com"      # Replace with your Gmail
EMAIL_PASSWORD = "vgqzxsjeqcgscsfd"        # Replace with your 16-character App Password
TO_EMAIL = "sainik2405@gmail.com"      # Replace with the email you want to test
STUDENT_NAME = "Test Student"

# ---------- CREATE EMAIL ----------
msg = EmailMessage()
msg['Subject'] = "Test Email - Attendance System"
msg['From'] = EMAIL_ADDRESS
msg['To'] = TO_EMAIL
msg.set_content(f"Hello {STUDENT_NAME},\n\nThis is a test email from the attendance system.\n\n- Attendance System")

# ---------- SEND EMAIL ----------
try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
    print(f"✅ Email successfully sent to {TO_EMAIL}")
except Exception as e:
    print(f"❌ Failed to send email: {e}")
