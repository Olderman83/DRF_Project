from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerator, IsOwner, IsOwnerOrModerator, IsOwnerOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

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
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

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
