from rest_framework import viewsets, filters, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Payment
from .serializers import (
    UserSerializer,
    PaymentSerializer,
    UserWithPaymentsSerializer
)
from .permissions import IsOwner


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """
        Разделение прав доступа для пользователей
        """
        if self.action == 'create':
            # Регистрация доступна всем
            permission_classes = [permissions.AllowAny]
        elif self.action in ['retrieve', 'list']:
            # Просмотр доступен всем авторизованным
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Изменение и удаление только своего профиля
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Выбор сериализатора в зависимости от действия
        """
        if self.action == 'retrieve':
            # Для детального просмотра используем расширенный сериализатор
            return UserWithPaymentsSerializer
        return UserSerializer

    def get_queryset(self):
        """
        Для списка пользователей возвращаем всех (только для админов),
        для обычных пользователей - только себя
        """
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related('user', 'course', 'lesson')
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'course', 'lesson']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']

    def get_permissions(self):
        """
        Платежи видят только владельцы или админы
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Обычные пользователи видят только свои платежи
        """
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)
