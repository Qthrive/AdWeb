from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import InvoiceRequest, Transaction
from Users.models import User, Notification
from decimal import Decimal
from django.utils import timezone
import models

@login_required
def invoice_request(request):
    user = request.user
    # 可开票金额（假设为账户余额，或可自定义逻辑）
    max_amount = getattr(user, 'balance', 0)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        company_name = request.POST.get('title')
        tax_number = request.POST.get('tax_number')
        email = request.POST.get('email')  # 模型暂未存储email，可后续扩展
        notes = request.POST.get('description', '')

        # 校验金额
        try:
            amount = Decimal(amount)
        except Exception:
            messages.error(request, '请输入有效的开票金额。')
            return redirect('payment:invoice')
        if amount <= 0 or amount > max_amount:
            messages.error(request, '开票金额必须大于0且不超过可开票金额。')
            return redirect('payment:invoice')
        if not company_name or not tax_number or not email:
            messages.error(request, '请填写所有必填项。')
            return redirect('payment:invoice')

        # 创建发票申请
        InvoiceRequest.objects.create(
            user=user,
            amount=amount,
            company_name=company_name,
            tax_number=tax_number,
            email=email,
            notes=notes,
        )
        messages.success(request, '发票申请已提交，等待处理。')
        return redirect('payment:invoice')

    # 查询历史记录，分页
    invoice_qs = InvoiceRequest.objects.filter(user=user).order_by('-request_date')
    paginator = Paginator(invoice_qs, 8)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)

    # 查询未读发票相关通知
    invoice_notifications = Notification.objects.filter(user=user, title__icontains='发票', status='unread')

    context = {
        'max_amount': max_amount,
        'invoices': invoices,
        'invoice_notifications': invoice_notifications,
    }
    return render(request, 'Payment/invoice.html', context)

@login_required
def balance(request):
    user = request.user
    # 账户余额
    balance = getattr(user, 'balance', 0)
    # 本月消费
    monthly_cost = Transaction.objects.filter(user=user, transaction_type='ad_spend', status='completed', created_at__month=timezone.now().month).aggregate(total=models.Sum('amount'))['total'] or 0
    # 本月充值
    monthly_recharge = Transaction.objects.filter(user=user, transaction_type='recharge', status='completed', created_at__month=timezone.now().month).aggregate(total=models.Sum('amount'))['total'] or 0
    # 交易记录分页
    transactions = Transaction.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(transactions, 10)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)
    context = {
        'user': user,
        'monthly_cost': monthly_cost,
        'monthly_recharge': monthly_recharge,
        'transactions': transactions_page,
    }
    return render(request, 'Payment/balance.html', context)

@login_required
def recharge(request):
    user = request.user
    if request.method == 'POST':
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')
        try:
            amount = Decimal(amount)
        except Exception:
            messages.error(request, '请输入有效的充值金额。')
            return redirect('payment:recharge')
        if amount <= 0:
            messages.error(request, '充值金额必须大于0。')
            return redirect('payment:recharge')
        # 创建充值记录
        tx = Transaction.objects.create(
            user=user,
            amount=amount,
            transaction_type='recharge',
            status='completed',
            description=description
        )
        # 增加用户余额
        user.balance = (user.balance or 0) + amount
        user.save()
        messages.success(request, f'充值成功，金额已到账。')
        return redirect('payment:balance')
    return render(request, 'Payment/recharge.html')

# 管理员权限判断

def is_admin(user):
    return hasattr(user, 'role') and user.role == 'admin'

@user_passes_test(is_admin)
def invoice_admin_list(request):
    # 管理员查看所有发票申请
    invoice_qs = InvoiceRequest.objects.all().order_by('-request_date')
    paginator = Paginator(invoice_qs, 12)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)
    context = {
        'invoices': invoices,
    }
    return render(request, 'Payment/invoice_admin_list.html', context)

@user_passes_test(is_admin)
def invoice_admin_review(request, invoice_id):
    invoice = get_object_or_404(InvoiceRequest, id=invoice_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        if action == 'approve':
            invoice.status = 'approved'
            invoice.process_date = timezone.now()
            invoice.notes = notes
            invoice.save()
            # 生成通知
            Notification.objects.create(
                user=invoice.user,
                title='发票申请已批准',
                content=f'您的发票申请（金额：¥{invoice.amount}，抬头：{invoice.company_name}）已批准。备注：{notes}',
                status='unread',
            )
            messages.success(request, '发票申请已批准。')
        elif action == 'reject':
            invoice.status = 'rejected'
            invoice.process_date = timezone.now()
            invoice.notes = notes
            invoice.save()
            # 生成通知
            Notification.objects.create(
                user=invoice.user,
                title='发票申请被拒绝',
                content=f'您的发票申请（金额：¥{invoice.amount}，抬头：{invoice.company_name}）被拒绝。备注：{notes}',
                status='unread',
            )
            messages.success(request, '发票申请已拒绝。')
        return redirect('payment:invoice_admin_list')
    context = {
        'invoice': invoice,
    }
    return render(request, 'Payment/invoice_admin_review.html', context)
