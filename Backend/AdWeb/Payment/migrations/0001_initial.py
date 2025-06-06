# Generated by Django 5.1.7 on 2025-05-10 07:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('AdPlace', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('company_name', models.CharField(max_length=200)),
                ('tax_number', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('pending', '待处理'), ('approved', '已批准'), ('rejected', '已拒绝'), ('issued', '已开具')], default='pending', max_length=20)),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('process_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoice_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '发票申请',
                'verbose_name_plural': '发票申请',
                'ordering': ['-request_date'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('transaction_type', models.CharField(choices=[('recharge', '充值'), ('ad_spend', '广告支出'), ('refund', '退款')], max_length=20)),
                ('status', models.CharField(choices=[('pending', '处理中'), ('completed', '已完成'), ('failed', '失败')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='AdPlace.ad')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '交易记录',
                'verbose_name_plural': '交易记录',
                'ordering': ['-created_at'],
            },
        ),
    ]
