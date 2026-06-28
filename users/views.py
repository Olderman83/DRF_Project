from rest_framework import viewsets, filters, generics
from django_filters.rest_framework import DjangoFilterBackend
from .models import User, Payment
from .serializers import (
    UserSerializer,
    PaymentSerializer,
    UserWithPaymentsSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'retrieve':
            # Для детального просмотра используем расширенный сериализатор
            return UserWithPaymentsSerializer
        return UserSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related('user', 'course', 'lesson')
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['payment_method', 'course', 'lesson']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']
