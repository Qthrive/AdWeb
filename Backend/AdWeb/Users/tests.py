from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .forms import RegistrationForm

User = get_user_model()


class RegistrationFormTestCase(TestCase):
    def setUp(self):
        # 创建一个已存在的用户用于测试邮箱唯一性
        User.objects.create_user(username='existinguser', email='existing@example.com', password='testpass')

    def test_form_fields_exist(self):
        """测试表单字段是否存在"""
        form = RegistrationForm()
        self.assertIn('email', form.fields)
        self.assertIn('username', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)

    def test_form_valid_data(self):
        """测试表单在有效数据下是否通过验证"""
        form_data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_password_mismatch(self):
        """测试密码不匹配时表单是否验证失败"""
        form_data = {
            'email': 'new@example.com',
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'differentpassword'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        # 修改预期错误信息为英文
        self.assertEqual(form.errors['password2'], ["The two password fields didn’t match."])

    def test_form_email_uniqueness(self):
        """测试邮箱唯一性检查"""
        form_data = {
            'email': 'existing@example.com',
            'username': 'newuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['email'], ["该邮箱已被注册"])