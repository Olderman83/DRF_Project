from rest_framework import serializers
from .models import User, Payment


class PaymentDetailedSerializer(serializers.ModelSerializer):
    """Детальный сериализатор для платежей с информацией о курсе/уроке"""
    course_details = serializers.SerializerMethodField()
    lesson_details = serializers.SerializerMethodField()
    payment_method_display = serializers.ReadOnlyField(source='get_payment_method_display')

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_date', 'amount', 'payment_method', 'payment_method_display',
            'course_details', 'lesson_details'
        ]

    def get_course_details(self, obj):
        if obj.course:
            from lms.serializers import CourseSerializer
            return CourseSerializer(obj.course).data
        return None

    def get_lesson_details(self, obj):
        if obj.lesson:
            from lms.serializers import LessonSerializer
            return LessonSerializer(obj.lesson).data
        return None


class UserSerializer(serializers.ModelSerializer):
    """Базовый сериализатор пользователя"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserWithPaymentsSerializer(UserSerializer):
    """Расширенный сериализатор пользователя с историей платежей"""
    payments_history = serializers.SerializerMethodField()
    total_payments_amount = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['payments_history', 'total_payments_amount']

    def get_payments_history(self, obj):
        payments = obj.payments.all().order_by('-payment_date')
        return PaymentDetailedSerializer(payments, many=True).data

    def get_total_payments_amount(self, obj):
        total = obj.payments.aggregate(total=models.Sum('amount'))['total']
        return float(total) if total else 0.0


class PaymentSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для платежей"""
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
