from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_url, YouTubeValidator


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'description', 'preview', 'video_url', 'course', 'owner']
        read_only_fields = ['id', 'owner']
        validators = [
            YouTubeValidator(field='video_url')
        ]

    def validate_video_url(self, value):
        """
        Валидация поля video_url с помощью функции-валидатора
        """
        return validate_youtube_url(value)


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'preview', 'description', 'lessons', 'lessons_count', 'owner', 'is_subscribed']
        read_only_fields = ['id', 'owner']

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """
        Проверка, подписан ли текущий пользователь на курс
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriptions.filter(user=request.user).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор для подписок
    """
    course_name = serializers.ReadOnlyField(source='course.name')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'user_email', 'course', 'course_name', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
