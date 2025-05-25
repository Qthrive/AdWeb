from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Invoice, InvoiceInfo, Transaction, InvoiceItem
from Users.models import User, Notification
from decimal import Decimal
from django.utils import timezone
from django.db import models

@login_required
def invoice_request(request):
    user = request.user
    # 可开票金额（假设为账户余额，或可自定义逻辑）
    max_amount = getattr(user, 'balance', 0)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        title = request.POST.get('title')
        tax_number = request.POST.get('tax_number')
        email = request.POST.get('email')
        address = request.POST.get('address', '')
        contact_name = request.POST.get('contact_name', '')
        contact_phone = request.POST.get('contact_phone', '')
        invoice_type = request.POST.get('invoice_type', 'normal')
        remark = request.POST.get('remark', '')

        # 校验金额
        try:
            amount = Decimal(amount)
        except Exception:
            messages.error(request, '请输入有效的开票金额。')
            return redirect('payment:invoice')
        if amount <= 0 or amount > max_amount:
            messages.error(request, '开票金额必须大于0且不超过可开票金额。')
            return redirect('payment:invoice')
        if not title or not tax_number or not email:
            messages.error(request, '请填写所有必填项。')
            return redirect('payment:invoice')

        # 获取或创建发票信息
        invoice_info, created = InvoiceInfo.objects.get_or_create(
            user=user,
            title=title,
            tax_number=tax_number,
            defaults={
                'address': address,
                'telephone': contact_phone,
                'is_default': True
            }
        )
        
        # 如果是新创建的发票信息，设置为默认
        if created:
            # 将其他发票信息设置为非默认
            InvoiceInfo.objects.filter(user=user).exclude(id=invoice_info.id).update(is_default=False)
        
        # 创建发票申请
        invoice = Invoice.objects.create(
            user=user,
            invoice_info=invoice_info,
            invoice_type=invoice_type,
            amount=amount,
            title=title,
            tax_number=tax_number,
            content='广告服务费',
            remark=remark,
            email=email,
            address=address,
            contact_name=contact_name,
            contact_phone=contact_phone,
            status='pending'
        )
        
        # 关联交易记录
        # 获取用户的广告支出交易记录，按时间倒序排列
        transactions = Transaction.objects.filter(
            user=user, 
            transaction_type='ad_spend',
            status='completed'
        ).order_by('-created_at')
        
        # 计算已经添加的金额
        added_amount = Decimal('0.00')
        
        # 为发票添加交易项目，直到达到发票金额
        for transaction in transactions:
            if added_amount >= amount:
                break
                
            # 计算本次可添加的金额
            item_amount = min(transaction.amount, amount - added_amount)
            
            # 创建发票项目
            InvoiceItem.objects.create(
                invoice=invoice,
                transaction=transaction,
                amount=item_amount
            )
            
            # 更新已添加金额
            added_amount += item_amount
        
        messages.success(request, '发票申请已提交，等待处理。')
        return redirect('payment:invoice')

    # 查询历史记录，分页
    invoice_qs = Invoice.objects.filter(user=user).order_by('-created_at')
    paginator = Paginator(invoice_qs, 8)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)
    
    # 获取用户的发票信息列表
    invoice_infos = InvoiceInfo.objects.filter(user=user).order_by('-is_default')

    # 查询未读发票相关通知
    invoice_notifications = Notification.objects.filter(user=user, title__icontains='发票', status='unread')

    context = {
        'max_amount': max_amount,
        'invoices': invoices,
        'invoice_infos': invoice_infos,
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
        payment_method = request.POST.get('payment_method', 'balance')
        description = request.POST.get('description', '')
        
        try:
            amount = Decimal(amount)
        except Exception:
            messages.error(request, '请输入有效的充值金额。')
            return redirect('payment:recharge')
        
        if amount <= 0:
            messages.error(request, '充值金额必须大于0。')
            return redirect('payment:recharge')

        try:
            # 创建充值交易记录
            transaction = Transaction.objects.create(
                user=user,
                amount=amount,
                description=description,
                transaction_type='recharge',
                payment_method=payment_method,
                status='completed'  # 模拟情况下，所有支付都直接完成
            )

            # 根据支付方式处理
            if payment_method == 'balance':
                # 余额支付直接更新账户
                user.balance = Decimal(user.balance or 0) + amount
                user.save()
                
                messages.success(request, f'充值成功！已向您的账户充值 ¥{amount}')
            else:
                # 模拟其他支付方式
                payment_method_display = dict(Transaction.PAYMENT_METHODS).get(payment_method)
                
                # 模拟支付成功
                transaction.status = 'completed'
                transaction.save()
                
                # 更新用户余额
                user.balance = Decimal(user.balance or 0) + amount
                user.save()
                
                messages.success(request, f'使用{payment_method_display}充值 ¥{amount} 成功！')                # 创建通知
            Notification.objects.create(
                user=user,
                title='充值成功',
                content=f'您已使用{transaction.get_payment_method_display()}成功充值 ¥{amount}，交易编号：{transaction.id}',
                status='unread'
            )
            
            return redirect('payment:balance')

        except Exception as e:
            messages.error(request, f'充值失败，请稍后重试。错误信息：{str(e)}')
            return redirect('payment:recharge')

    # 准备支付方式选项
    payment_methods = Transaction.PAYMENT_METHODS
    
    return render(request, 'Payment/recharge.html', {
        'payment_methods': payment_methods
    })

# 管理员权限判断

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def invoice_admin_list(request):
    # 管理员查看所有发票申请
    invoice_qs = Invoice.objects.all().order_by('-created_at')
    paginator = Paginator(invoice_qs, 12)
    page = request.GET.get('page')
    invoices = paginator.get_page(page)
    context = {
        'invoices': invoices,
    }
    return render(request, 'Payment/invoice_admin_list.html', context)

@user_passes_test(is_admin)
def invoice_admin_review(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_remark = request.POST.get('admin_remark', '')
        
        if action == 'approve':
            invoice.status = 'processing'
            invoice.admin_remark = admin_remark
            invoice.save()
            # 生成通知
            Notification.objects.create(
                user=invoice.user,
                title='发票申请已批准',
                content=f'您的发票申请（金额：¥{invoice.amount}，抬头：{invoice.title}）已批准，正在处理中。',
                status='unread',
            )
            messages.success(request, '发票申请已批准，状态更新为处理中。')
        elif action == 'reject':
            invoice.status = 'rejected'
            invoice.admin_remark = admin_remark
            invoice.save()
            # 生成通知
            Notification.objects.create(
                user=invoice.user,
                title='发票申请被拒绝',
                content=f'您的发票申请（金额：¥{invoice.amount}，抬头：{invoice.title}）被拒绝。原因：{admin_remark}',
                status='unread',
            )
            messages.success(request, '发票申请已拒绝。')
        elif action == 'complete':
            invoice_number = request.POST.get('invoice_number', '')
            invoice_date = request.POST.get('invoice_date')
            express_company = request.POST.get('express_company', '')
            tracking_number = request.POST.get('tracking_number', '')
            
            if not invoice_number or not invoice_date:
                messages.error(request, '请填写发票号码和开票日期。')
                return redirect('payment:invoice_admin_review', invoice_id=invoice.id)
                
            try:
                invoice_date = timezone.datetime.strptime(invoice_date, '%Y-%m-%d').date()
            except:
                messages.error(request, '请输入有效的开票日期（格式：YYYY-MM-DD）。')
                return redirect('payment:invoice_admin_review', invoice_id=invoice.id)
                
            invoice.status = 'completed'
            invoice.invoice_number = invoice_number
            invoice.invoice_date = invoice_date
            invoice.express_company = express_company
            invoice.tracking_number = tracking_number
            invoice.admin_remark = admin_remark
            invoice.save()
            
            # 生成通知
            notification_content = f'您的发票申请（金额：¥{invoice.amount}，抬头：{invoice.title}）已开具完成。'
            if tracking_number:
                notification_content += f'快递公司：{express_company}，快递单号：{tracking_number}。'
                
            Notification.objects.create(
                user=invoice.user,
                title='发票已开具',
                content=notification_content,
                status='unread',
            )
            messages.success(request, '发票已开具完成，已通知用户。')
        
        return redirect('payment:invoice_admin_list')
        
    # 获取发票关联的交易记录
    invoice_items = invoice.items.all().select_related('transaction')
    
    context = {
        'invoice': invoice,
        'invoice_items': invoice_items,
    }
    return render(request, 'Payment/invoice_admin_review.html', context)

@login_required
def invoice_detail(request, invoice_id):
    """查看发票详情"""
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    # 获取发票关联的交易记录
    invoice_items = invoice.items.all().select_related('transaction')
    
    context = {
        'invoice': invoice,
        'invoice_items': invoice_items,
    }
    return render(request, 'Payment/invoice_detail.html', context)

@login_required
def invoice_cancel(request, invoice_id):
    """取消发票申请"""
    invoice = get_object_or_404(Invoice, id=invoice_id, user=request.user)
    
    if invoice.status != 'pending':
        messages.error(request, '只能取消待处理的发票申请。')
        return redirect('payment:invoice')
        
    if request.method == 'POST':
        invoice.status = 'cancelled'
        invoice.save()
        messages.success(request, '发票申请已取消。')
        return redirect('payment:invoice')
        
    context = {
        'invoice': invoice,
    }
    return render(request, 'Payment/invoice_cancel.html', context)

@login_required
def invoice_info_manage(request):
    """管理发票信息"""
    user = request.user
    invoice_infos = InvoiceInfo.objects.filter(user=user).order_by('-is_default')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            title = request.POST.get('title')
            tax_number = request.POST.get('tax_number')
            address = request.POST.get('address', '')
            telephone = request.POST.get('telephone', '')
            bank_name = request.POST.get('bank_name', '')
            bank_account = request.POST.get('bank_account', '')
            is_default = request.POST.get('is_default') == 'on'
            
            if not title or not tax_number:
                messages.error(request, '请填写发票抬头和税号。')
                return redirect('payment:invoice_info_manage')
                
            # 创建新的发票信息
            invoice_info = InvoiceInfo.objects.create(
                user=user,
                title=title,
                tax_number=tax_number,
                address=address,
                telephone=telephone,
                bank_name=bank_name,
                bank_account=bank_account,
                is_default=is_default
            )
            
            # 如果设置为默认，更新其他发票信息
            if is_default:
                InvoiceInfo.objects.filter(user=user).exclude(id=invoice_info.id).update(is_default=False)
                
            messages.success(request, '发票信息添加成功。')
            return redirect('payment:invoice_info_manage')
            
        elif action == 'set_default':
            info_id = request.POST.get('info_id')
            if info_id:
                # 设置指定的发票信息为默认
                InvoiceInfo.objects.filter(user=user, id=info_id).update(is_default=True)
                # 其他发票信息设置为非默认
                InvoiceInfo.objects.filter(user=user).exclude(id=info_id).update(is_default=False)
                messages.success(request, '默认发票信息已更新。')
            
            return redirect('payment:invoice_info_manage')
            
    context = {
        'invoice_infos': invoice_infos,
    }
    return render(request, 'Payment/invoice_info_manage.html', context)

@login_required
def invoice_info_edit(request, info_id):
    """编辑发票信息"""
    user = request.user
    invoice_info = get_object_or_404(InvoiceInfo, id=info_id, user=user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        tax_number = request.POST.get('tax_number')
        address = request.POST.get('address', '')
        telephone = request.POST.get('telephone', '')
        bank_name = request.POST.get('bank_name', '')
        bank_account = request.POST.get('bank_account', '')
        is_default = request.POST.get('is_default') == 'on'
        
        if not title or not tax_number:
            messages.error(request, '请填写发票抬头和税号。')
            return redirect('payment:invoice_info_edit', info_id=info_id)
            
        # 更新发票信息
        invoice_info.title = title
        invoice_info.tax_number = tax_number
        invoice_info.address = address
        invoice_info.telephone = telephone
        invoice_info.bank_name = bank_name
        invoice_info.bank_account = bank_account
        invoice_info.is_default = is_default
        invoice_info.save()
        
        # 如果设置为默认，更新其他发票信息
        if is_default:
            InvoiceInfo.objects.filter(user=user).exclude(id=invoice_info.id).update(is_default=False)
            
        messages.success(request, '发票信息更新成功。')
        return redirect('payment:invoice_info_manage')
        
    context = {
        'invoice_info': invoice_info,
    }
    return render(request, 'Payment/invoice_info_edit.html', context)

@login_required
def invoice_info_delete(request, info_id):
    """删除发票信息"""
    user = request.user
    invoice_info = get_object_or_404(InvoiceInfo, id=info_id, user=user)
    
    # 检查是否有关联的发票
    if Invoice.objects.filter(invoice_info=invoice_info).exists():
        messages.error(request, '该发票信息已被使用，无法删除。')
        return redirect('payment:invoice_info_manage')
    
    if request.method == 'POST':
        # 如果是默认发票信息，需要设置其他发票信息为默认
        if invoice_info.is_default:
            other_info = InvoiceInfo.objects.filter(user=user).exclude(id=info_id).first()
            if other_info:
                other_info.is_default = True
                other_info.save()
                
        # 删除发票信息
        invoice_info.delete()
        messages.success(request, '发票信息已删除。')
        return redirect('payment:invoice_info_manage')
        
    context = {
        'invoice_info': invoice_info,
    }
    return render(request, 'Payment/invoice_info_delete.html', context)
