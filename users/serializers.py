from rest_framework import serializers
from django.db import models
from django.contrib.auth import get_user_model
from .models import Payment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined', 'password',
                  'password_confirm']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'password_confirm': {'write_only': True, 'required': False},
        }

    def validate(self, data):
        """
        Проверка совпадения паролей
        """
        password = data.get('password')
        password_confirm = data.get('password_confirm')

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        """
        Создание пользователя с хешированием пароля
        """
        # Удаляем password_confirm из данных
        validated_data.pop('password_confirm', None)
        # Получаем пароль
        password = validated_data.pop('password', None)
        # Создаем пользователя
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Обновление пользователя с хешированием пароля
        """
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.ReadOnlyField(source='user.email')
    course_name = serializers.ReadOnlyField(source='course.name', default=None)
    lesson_name = serializers.ReadOnlyField(source='lesson.name', default=None)
    payment_method_display = serializers.ReadOnlyField(source='get_payment_method_display')

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'payment_date',
            'course', 'course_name', 'lesson', 'lesson_name',
            'amount', 'payment_method', 'payment_method_display',
            'created_at', 'payment_status'
        ]
        read_only_fields = ['id', 'created_at']


class UserWithPaymentsSerializer(UserSerializer):
    payments_history = serializers.SerializerMethodField()
    total_payments_amount = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['payments_history', 'total_payments_amount']

    def get_payments_history(self, obj):
        payments = obj.payments.all().order_by('-payment_date')
        return PaymentSerializer(payments, many=True).data

    def get_total_payments_amount(self, obj):
        total = obj.payments.aggregate(total=models.Sum('amount'))['total']
        return float(total) if total else 0.0
