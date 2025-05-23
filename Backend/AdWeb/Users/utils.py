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

def send_audit_result_email(user, action, reason):
    """发送审核结果邮件给用户
    
    :param user: 用户对象
    :param action: 审核结果 ('approve' 或 'reject')
    :param reason: 审核意见
    """
    if action == 'approve':
        subject = '恭喜！您的注册申请已通过审核'
        message = f'''尊敬的{user.username}：

您好！我们很高兴地通知您，您在AdWeb广告管理平台的注册申请已通过审核。

审核意见：{reason}

您现在可以使用您的邮箱（{user.email}）和密码登录平台。

如有任何问题，请随时联系我们的客服团队。

祝您使用愉快！

AdWeb广告管理平台团队'''
    else:
        subject = '很抱歉，您的注册申请未通过审核'
        message = f'''尊敬的{user.username}：

您好！非常抱歉地通知您，您在AdWeb广告管理平台的注册申请未通过审核。

未通过原因：{reason}

您可以根据上述原因进行调整后重新注册。如有任何疑问，请联系我们的客服团队。

AdWeb广告管理平台团队'''

    send_mail(
        subject,
        message,
        'qthrive@126.com',  # 发件人邮箱
        [user.email],  # 收件人邮箱
        fail_silently=False,
    )