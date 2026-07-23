from rest_framework import viewsets, filters, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Payment
from .serializers import (
    UserSerializer,
    PaymentSerializer,
    UserWithPaymentsSerializer
)
from .permissions import IsOwner

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.

    Доступные действия:
    - list: Просмотр списка пользователей (только для админов)
    - retrieve: Просмотр профиля пользователя
    - create: Регистрация нового пользователя
    - update: Обновление профиля (только свой)
    - partial_update: Частичное обновление профиля (только свой)
    - destroy: Удаление профиля (только свой)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=UserSerializer,
        responses={
            201: UserSerializer(),
            400: "Ошибка валидации (пароли не совпадают)"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['retrieve', 'list']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserWithPaymentsSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        password = self.request.data.get('password')
        if password:
            user.set_password(password)
            user.save()

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления платежами.

    Доступные действия:
    - list: Просмотр платежей (только свои для обычных пользователей, все для админов)
    - retrieve: Просмотр конкретного платежа
    - create: Создание платежа (только для админов)
    """
    queryset = Payment.objects.all().select_related('user', 'course', 'lesson')
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'course', 'lesson', 'payment_status']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']

    @swagger_auto_schema(
        operation_description="Создать новый платеж",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['amount'],
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID пользователя'
                ),
                'course_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID курса (если оплачивается курс)'
                ),
                'lesson_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID урока (если оплачивается урок)'
                ),
                'amount': openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description='Сумма платежа'
                ),
                'payment_method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Способ оплаты (CASH, TRANSFER, STRIPE)'
                ),
            }
        ),
        responses={
            201: PaymentSerializer(),
            400: "Ошибка валидации",
            403: "Доступ запрещен (только для администраторов)"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)
