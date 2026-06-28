from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'name', 'description', 'preview', 'video_url', 'course']
        read_only_fields = ['id']


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'preview', 'description', 'lessons', 'lessons_count']
        read_only_fields = ['id']

    def get_lessons_count(self, obj):
        return obj.lessons.count()
