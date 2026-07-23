from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Course, Lesson, Subscription
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from .paginators import CoursePaginator, LessonPaginator
from users.permissions import IsModerator, IsOwner, IsOwnerOrModerator


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления курсами.

    Доступные действия:
    - list: Просмотр списка курсов
    - retrieve: Просмотр конкретного курса
    - create: Создание нового курса (только для обычных пользователей)
    - update: Полное обновление курса (владелец или модератор)
    - partial_update: Частичное обновление курса (владелец или модератор)
    - destroy: Удаление курса (только владелец)
    """
    serializer_class = CourseSerializer
    pagination_class = CoursePaginator

    def get_queryset(self):
        """Фильтрация курсов в зависимости от прав пользователя."""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    @swagger_auto_schema(
        operation_description="Получить список всех курсов",
        responses={200: CourseSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый курс",
        request_body=CourseSerializer,
        responses={
            201: CourseSerializer(),
            400: "Ошибка валидации",
            403: "Доступ запрещен (модераторы не могут создавать курсы)"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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


class LessonViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления уроками.

    Доступные действия аналогичны CourseViewSet.
    """
    serializer_class = LessonSerializer
    pagination_class = LessonPaginator

    def get_queryset(self):
        """Фильтрация уроков в зависимости от прав пользователя."""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    @swagger_auto_schema(
        operation_description="Создать новый урок",
        request_body=LessonSerializer,
        responses={
            201: LessonSerializer(),
            400: "Ошибка валидации (проверка ссылки на YouTube)",
            403: "Доступ запрещен"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

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


class SubscriptionView(APIView):
    """
    Эндпоинт для управления подписками на обновления курса.

    POST: Создание или удаление подписки на курс.
    """
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
        """
        Создание или удаление подписки.
        """
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
