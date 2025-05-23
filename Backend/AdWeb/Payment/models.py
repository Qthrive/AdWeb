from django.db import models
from Users.models import User
from AdPlace.models import Ad

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('recharge', '充值'),
        ('ad_spend', '广告支出'),
        ('refund', '退款')
    ]

    STATUS_CHOICES = [
        ('pending', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败')
    ]

    PAYMENT_METHODS = [
        ('balance', '余额支付'),
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
        ('bank', '银行转账')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='balance')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ad = models.ForeignKey(Ad, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '交易记录'
        verbose_name_plural = '交易记录'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_transaction_type_display()} - {self.amount}"

class InvoiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('issued', '已开具')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoice_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    company_name = models.CharField(max_length=200)
    tax_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    process_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    email = models.EmailField(verbose_name='接收邮箱', default='')

    class Meta:
        verbose_name = '发票申请'
        verbose_name_plural = '发票申请'
        ordering = ['-request_date']

    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.get_status_display()}"
