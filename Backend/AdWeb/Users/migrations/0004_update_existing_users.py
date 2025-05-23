from django.db import migrations

def update_existing_users(apps, schema_editor):
    User = apps.get_model('Users', 'User')
    # 更新所有现有用户为已审核通过的状态
    User.objects.all().update(
        audit_status='approved',
        user_type='admin',  # 将现有用户设置为管理员
        is_verified=True
    )

class Migration(migrations.Migration):

    dependencies = [
        ('Users', '0003_user_audit_status_user_audit_time_user_device_info_and_more'),
    ]

    operations = [
        migrations.RunPython(update_existing_users),
    ]
