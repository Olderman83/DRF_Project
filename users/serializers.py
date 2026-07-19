from django.db import models
from rest_framework import serializers
from .models import User, Payment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }


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
            'created_at'
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
