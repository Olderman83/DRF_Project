from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.core.management import call_command
from io import StringIO
from datetime import datetime
from .models import User, Payment
from lms.models import Course, Lesson

User = get_user_model()


class UserBaseTest(TestCase):
    """Базовый класс для тестов пользователей"""

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='+79001234567',
            city='Moscow'
        )

        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )

        self.moderator = User.objects.create_user(
            email='moderator@example.com',
            password='testpass123'
        )
        moderator_group, created = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(moderator_group)

        # Создаем курсы для тестов платежей
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            owner=self.user
        )

        self.lesson = Lesson.objects.create(
            name='Test Lesson',
            description='Test Lesson Description',
            video_url='https://www.youtube.com/watch?v=test123',
            course=self.course,
            owner=self.user
        )

        # Создаем платежи
        self.payment1 = Payment.objects.create(
            user=self.user,
            amount=1500.00,
            payment_method='CASH',
            course=self.course,
            payment_date=datetime(2026, 1, 15, 10, 30)
        )

        self.payment2 = Payment.objects.create(
            user=self.user,
            amount=750.00,
            payment_method='TRANSFER',
            lesson=self.lesson,
            payment_date=datetime(2026, 1, 20, 14, 15)
        )

        # Настраиваем клиенты
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin_user)

        self.moderator_client = APIClient()
        self.moderator_client.force_authenticate(user=self.moderator)


class UserViewSetTest(UserBaseTest):
    """Тесты для UserViewSet"""

    def test_create_user(self):
        """Проверка: регистрация нового пользователя"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'phone': '+79009999999',
            'city': 'Moscow'
        }
        response = self.user_client.post(reverse('user-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 4)
        self.assertEqual(response.data['email'], 'newuser@example.com')

    def test_create_user_password_mismatch(self):
        """Проверка: ошибка при несовпадении паролей"""
        data = {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.user_client.post(reverse('user-list'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', str(response.data))

    def test_list_users_as_admin(self):
        """Проверка: администратор видит всех пользователей"""
        response = self.admin_client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # user, admin, moderator

    def test_list_users_as_user(self):
        """Проверка: обычный пользователь видит только себя"""
        response = self.user_client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'user@example.com')


class PaymentViewSetTest(UserBaseTest):
    """Тесты для PaymentViewSet"""

    def test_list_payments_as_owner(self):
        """Проверка: пользователь видит свои платежи"""
        response = self.user_client.get(reverse('payment-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_payment_as_user(self):
        """Проверка: обычный пользователь не может создавать платежи"""
        data = {
            'user': self.user.id,
            'amount': 500.00,
            'payment_method': 'CASH',
            'course': self.course.id
        }
        response = self.user_client.post(reverse('payment-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PaymentModelTest(TestCase):
    """Тесты для модели Payment"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            owner=self.user
        )

    def test_payment_validation_course_or_lesson(self):
        """Проверка: валидация модели"""
        from django.core.exceptions import ValidationError

        # Платеж без курса и урока должен вызвать ошибку
        payment = Payment(
            user=self.user,
            amount=1000.00,
            payment_method='CASH'
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()

        # Платеж с обоими полями также должен вызвать ошибку
        payment = Payment(
            user=self.user,
            amount=1000.00,
            payment_method='CASH',
            course=self.course,
            lesson=self.course.lessons.first()
        )
        with self.assertRaises(ValidationError):
            payment.full_clean()


class UserModelTest(TestCase):
    """Тесты для модели User"""

    def test_create_user(self):
        """Проверка: создание пользователя"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Проверка: создание суперпользователя"""
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class AuthenticationTest(UserBaseTest):
    """Тесты для аутентификации"""

    def test_jwt_token_obtain(self):
        """Проверка: получение JWT токена"""
        response = self.user_client.post(
            reverse('token_obtain_pair'),
            {'email': 'user@example.com', 'password': 'testpass123'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)


class PermissionTest(UserBaseTest):
    """Тесты для прав доступа"""

    def test_is_owner_permission(self):
        """Проверка: проверка на владельца"""
        from users.permissions import IsOwner

        permission = IsOwner()

        # Владелец должен иметь доступ
        request = type('Request', (), {'user': self.user})()
        self.assertTrue(permission.has_object_permission(
            request, None, self.course
        ))

        # Другой пользователь не должен иметь доступ
        request = type('Request', (), {'user': self.moderator})()
        self.assertFalse(permission.has_object_permission(
            request, None, self.course
        ))

