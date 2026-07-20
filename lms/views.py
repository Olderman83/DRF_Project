from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsOwner, IsOwnerOrModerator, IsOwnerOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        """
        Возвращаем курсы в зависимости от прав пользователя:
        - Модератор: все курсы
        - Обычный пользователь: только свои курсы
        """
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def get_permissions(self):
        """
        Разделение прав доступа в зависимости от action
        """
        if self.action in ['list', 'retrieve']:
            # Просмотр доступен всем авторизованным пользователям
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            # Создание доступно только не-модераторам
            permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            # Изменение доступно владельцу или модератору
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            # Удаление доступно только владельцу
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Привязка владельца к создаваемому курсу
        """
        serializer.save(owner=self.request.user)


class LessonViewSet(viewsets.ModelViewSet):
    serializer_class = LessonSerializer

    def get_queryset(self):
        """
        Возвращаем уроки в зависимости от прав пользователя:
        - Модератор: все уроки
        - Обычный пользователь: только свои уроки
        """
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        """
        Разделение прав доступа в зависимости от action
        """
        if self.action in ['list', 'retrieve']:
            # Просмотр доступен всем авторизованным пользователям
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
            # Создание доступно только не-модераторам
            permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            # Изменение доступно владельцу или модератору
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            # Удаление доступно только владельцу
            permission_classes = [permissions.IsAuthenticated, IsOwner]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """
        Привязка владельца к создаваемому уроку
        """
        serializer.save(owner=self.request.user)
