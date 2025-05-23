import random
import string
from django.core.mail import send_mail
from .models import ValidationCode
from django.utils import timezone

def generate_code(length=6):
    """Generate a random verification code."""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(user):
    """Send a verification email to the user."""
    code = generate_code()
    expire_at = timezone.now() + timezone.timedelta(minutes=10)  # Code expires in 10 minutes
    ValidationCode.objects.update_or_create(
        user=user,
        defaults={'code': code, 'expire_at': expire_at}
    )
    # send email
    send_mail(
        '邮箱验证',
        f'您的验证码是: {code}。请在10分钟内使用。',
        'qthrive@126.com',
        [user.email],
        fail_silently=False,
    )