from django.db import models
from django.utils import timezone
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

class InvoiceInfo(models.Model):
    """发票信息"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoice_infos', verbose_name='用户')
    title = models.CharField(max_length=100, verbose_name='发票抬头')
    tax_number = models.CharField(max_length=30, verbose_name='税号')
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name='地址')
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name='电话')
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='开户银行')
    bank_account = models.CharField(max_length=30, blank=True, null=True, verbose_name='银行账号')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '发票信息'
        verbose_name_plural = '发票信息'

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Invoice(models.Model):
    """发票申请记录"""
    INVOICE_TYPE_CHOICES = (
        ('normal', '增值税普通发票'),
        ('special', '增值税专用发票'),
        ('electronic', '电子发票'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已开具'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', verbose_name='申请用户')
    invoice_info = models.ForeignKey(InvoiceInfo, on_delete=models.PROTECT, verbose_name='发票信息')
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES, default='normal', verbose_name='发票类型')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='发票金额')
    title = models.CharField(max_length=100, verbose_name='发票抬头')
    tax_number = models.CharField(max_length=30, verbose_name='税号')
    content = models.CharField(max_length=100, default='广告服务费', verbose_name='发票内容')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    remark = models.TextField(blank=True, null=True, verbose_name='备注')
    email = models.EmailField(verbose_name='接收邮箱')
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name='邮寄地址')
    contact_name = models.CharField(max_length=50, blank=True, null=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='联系电话')
    invoice_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='发票号码')
    invoice_date = models.DateField(blank=True, null=True, verbose_name='开票日期')
    express_company = models.CharField(max_length=50, blank=True, null=True, verbose_name='快递公司')
    tracking_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='快递单号')
    admin_remark = models.TextField(blank=True, null=True, verbose_name='管理员备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # 新增字段，用于存储电子发票PDF文件路径
    invoice_pdf = models.FileField(upload_to='invoices/', blank=True, null=True, verbose_name='电子发票PDF')
    
    class Meta:
        verbose_name = '发票'
        verbose_name_plural = '发票'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.amount} - {self.get_status_display()}"

class InvoiceItem(models.Model):
    """发票包含的消费项目"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name='发票')
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name='invoice_items', verbose_name='交易记录')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='金额')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '发票项目'
        verbose_name_plural = '发票项目'
        
    def __str__(self):
        return f"{self.invoice.title} - {self.amount}"
