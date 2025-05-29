import pyotp
import qrcode
from io import BytesIO
import base64
from django.conf import settings
from django.core.mail import send_mail
import random
import string

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_email_verification(email, code):
    """Send verification code via email"""
    try:
        subject = 'Your Verification Code'
        message = f'Your verification code is: {code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [email]
        
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def generate_totp_secret():
    """Generate a new TOTP secret"""
    return pyotp.random_base32()

def generate_totp_uri(secret, username):
    """Generate TOTP URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name="Ticketing System"
    )

def generate_qr_code(uri):
    """Generate QR code image from TOTP URI"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def verify_totp(secret, code):
    """Verify TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code) 