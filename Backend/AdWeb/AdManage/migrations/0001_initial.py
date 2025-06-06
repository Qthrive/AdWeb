# Generated by Django 5.1.7 on 2025-05-10 07:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='活动名称')),
                ('budget', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='总预算')),
                ('start_date', models.DateTimeField(verbose_name='开始时间')),
                ('end_date', models.DateTimeField(verbose_name='结束时间')),
                ('status', models.CharField(choices=[('active', '进行中'), ('paused', '已暂停'), ('ended', '已结束'), ('deleted', '已删除')], default='active', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('advertiser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '广告活动',
                'verbose_name_plural': '广告活动',
                'ordering': ['-created_at'],
            },
        ),
    ]
