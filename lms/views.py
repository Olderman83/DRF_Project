from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Course, Lesson, Subscription
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from .paginators import CoursePaginator, LessonPaginator
from users.permissions import IsModerator, IsOwner, IsOwnerOrModerator
from users.tasks import send_course_update_notification


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    pagination_class = CoursePaginator

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """
        При обновлении курса отправляем уведомления подписанным пользователям
        """
        course = self.get_object()
        updated_course = serializer.save()

        # Проверяем, что курс не обновлялся более 4 часов
        if course.updated_at:
            time_since_update = timezone.now() - course.updated_at
            if time_since_update < timedelta(hours=4):
                # Если обновление было менее 4 часов назад, не отправляем уведомление
                return

        # Получаем email всех подписанных пользователей
        subscribers = Subscription.objects.filter(course=course).select_related('user')
        subscriber_emails = [sub.user.email for sub in subscribers if sub.user.email]

        if subscriber_emails:
            # Отправляем задачу на отправку уведомлений асинхронно
            send_course_update_notification.delay(
                course_id=course.id,
                course_name=course.name,
                user_emails=subscriber_emails
            )


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer
    pagination_class = LessonPaginator

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """
        При обновлении урока проверяем, нужно ли отправлять уведомление о курсе
        """
        lesson = self.get_object()
        updated_lesson = serializer.save()

        # Проверяем, не обновлялся ли курс в течение последних 4 часов
        course = lesson.course
        if course.updated_at:
            time_since_update = timezone.now() - course.updated_at
            if time_since_update < timedelta(hours=4):
                # Если курс обновлялся менее 4 часов назад, не отправляем уведомление
                return

        # Получаем email всех подписанных пользователей
        subscribers = Subscription.objects.filter(course=course).select_related('user')
        subscriber_emails = [sub.user.email for sub in subscribers if sub.user.email]

        if subscriber_emails:
            # Отправляем задачу на отправку уведомлений асинхронно
            send_course_update_notification.delay(
                course_id=course.id,
                course_name=course.name,
                user_emails=subscriber_emails
            )


class SubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Создать или удалить подписку на курс",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_id'],
            properties={
                'course_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID курса, на который нужно подписаться'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                examples={
                    "application/json": {
                        "message": "Подписка добавлена"
                    }
                }
            ),
            400: "Не указан course_id или курс не существует",
            401: "Неавторизованный доступ"
        }
    )
    def post(self, request):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "Необходимо указать course_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, id=course_id)

        subscription = Subscription.objects.filter(
            user=user,
            course=course
        )

        if subscription.exists():
            subscription.delete()
            message = "Подписка удалена"
        else:
            Subscription.objects.create(user=user, course=course)
            message = "Подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)
