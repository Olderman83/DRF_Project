from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch
from .models import Course, Lesson, Subscription
from .serializers import CourseSerializer, LessonSerializer

User = get_user_model()


class LMSBaseTest(TestCase):
    """Базовый класс для тестов LMS с подготовкой данных"""

    def setUp(self):
        # Создаем пользователей
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.moderator = User.objects.create_user(
            email='moderator@example.com',
            password='testpass123',
            first_name='Moder',
            last_name='Ator'
        )

        # Создаем группу модераторов и добавляем пользователя
        moderator_group, created = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(moderator_group)

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )

        # Создаем курс
        self.course = Course.objects.create(
            name='Test Course',
            description='Test Description',
            owner=self.user
        )

        # Создаем урок
        self.lesson = Lesson.objects.create(
            name='Test Lesson',
            description='Test Lesson Description',
            video_url='https://www.youtube.com/watch?v=test123',
            course=self.course,
            owner=self.user
        )

        # Создаем подписку
        self.subscription = Subscription.objects.create(
            user=self.user,
            course=self.course
        )

        # Настраиваем клиенты
        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.moderator_client = APIClient()
        self.moderator_client.force_authenticate(user=self.moderator)

        self.other_client = APIClient()
        self.other_client.force_authenticate(user=self.other_user)


class CourseViewSetTest(LMSBaseTest):
    """Тесты для CourseViewSet"""

    def test_list_courses_as_owner(self):
        """Проверка: владелец видит свои курсы"""
        response = self.user_client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Course')

    def test_update_course_as_owner(self):
        """Проверка: владелец может редактировать свой курс"""
        data = {'name': 'Updated Course Name'}
        response = self.user_client.patch(
            reverse('course-detail', args=[self.course.id]),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.name, 'Updated Course Name')

    def test_delete_course_as_owner(self):
        """Проверка: владелец может удалить свой курс"""
        response = self.user_client.delete(
            reverse('course-detail', args=[self.course.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 0)

    def test_course_pagination(self):
        """Проверка: пагинация курсов"""
        # Создаем еще курсы
        for i in range(6):
            Course.objects.create(
                name=f'Course {i}',
                description=f'Description {i}',
                owner=self.user
            )

        response = self.user_client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)  # page_size=5
        self.assertTrue('next' in response.data)

    def test_course_lessons_count(self):
        """Проверка: подсчет количества уроков в курсе"""
        response = self.user_client.get(reverse('course-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['lessons_count'], 1)


class LessonViewSetTest(LMSBaseTest):
    """Тесты для LessonViewSet"""

    def test_list_lessons_as_owner(self):
        """Проверка: владелец видит свои уроки"""
        response = self.user_client.get(reverse('lesson-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Lesson')

    def test_update_lesson_as_owner(self):
        """Проверка: владелец может редактировать свой урок"""
        data = {'name': 'Updated Lesson Name'}
        response = self.user_client.patch(
            reverse('lesson-detail', args=[self.lesson.id]),
            data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.name, 'Updated Lesson Name')

    def test_delete_lesson_as_owner(self):
        """Проверка: владелец может удалить свой урок"""
        response = self.user_client.delete(
            reverse('lesson-detail', args=[self.lesson.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_lesson_pagination(self):
        """Проверка: пагинация уроков"""
        # Создаем еще уроки
        for i in range(11):
            Lesson.objects.create(
                name=f'Lesson {i}',
                description=f'Description {i}',
                video_url='https://www.youtube.com/watch?v=test123',
                course=self.course,
                owner=self.user
            )

        response = self.user_client.get(reverse('lesson-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)  # page_size=10
        self.assertTrue('next' in response.data)

    def test_lesson_youtube_validator_youtube_com(self):
        """Проверка: допустимая ссылка на YouTube"""
        data = {
            'name': 'Valid Lesson',
            'description': 'Valid Description',
            'video_url': 'https://www.youtube.com/watch?v=valid123',
            'course': self.course.id
        }
        response = self.user_client.post(reverse('lesson-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class SubscriptionViewTest(LMSBaseTest):
    """Тесты для SubscriptionView"""

    def test_create_subscription(self):
        """Проверка: создание подписки"""
        # Создаем новый курс для подписки
        new_course = Course.objects.create(
            name='New Course',
            description='New Description',
            owner=self.other_user
        )

        data = {'course_id': new_course.id}
        response = self.user_client.post(reverse('subscription'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Подписка добавлена')

        # Проверяем создание подписки
        subscription_exists = Subscription.objects.filter(
            user=self.user,
            course=new_course
        ).exists()
        self.assertTrue(subscription_exists)

    def test_subscription_unauthorized(self):
        """Проверка: неавторизованный пользователь не может подписаться"""
        client = APIClient()
        data = {'course_id': self.course.id}
        response = client.post(reverse('subscription'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CourseSerializerTest(TestCase):
    """Тесты для CourseSerializer"""

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

    def test_course_serializer_with_lessons_count(self):
        """Проверка: сериализатор курса содержит количество уроков"""
        # Создаем уроки
        Lesson.objects.create(
            name='Lesson 1',
            description='Description 1',
            video_url='https://www.youtube.com/watch?v=test1',
            course=self.course,
            owner=self.user
        )
        Lesson.objects.create(
            name='Lesson 2',
            description='Description 2',
            video_url='https://www.youtube.com/watch?v=test2',
            course=self.course,
            owner=self.user
        )

        serializer = CourseSerializer(self.course)
        self.assertEqual(serializer.data['lessons_count'], 2)
        self.assertEqual(len(serializer.data['lessons']), 2)
