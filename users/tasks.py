from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


@shared_task
def send_course_update_notification(course_id, course_name, user_emails):
    """
    Задача для отправки уведомлений об обновлении курса
    """
    if not user_emails:
        return f"No users to notify for course {course_name}"

    subject = f"Обновление курса: {course_name}"
    message = (
        f"Здравствуйте!\n\n"
        f"Курс '{course_name}' был обновлен.\n"
        f"Новые материалы уже доступны.\n\n"
        f"С уважением,\n"
        f"Команда LMS"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=user_emails,
            fail_silently=False,
        )
        return f"Notifications sent to {len(user_emails)} users for course {course_name}"
    except Exception as e:
        return f"Error sending notifications: {str(e)}"


@shared_task
def block_inactive_users(days=30):
    """
    Задача для блокировки неактивных пользователей

    Args:
        days (int): Количество дней бездействия для блокировки
    """
    threshold_date = timezone.now() - timedelta(days=days)

    # Находим пользователей, которые не заходили более days дней и активны
    inactive_users = User.objects.filter(
        Q(last_login__lt=threshold_date) | Q(last_login__isnull=True),
        is_active=True,
        is_superuser=False,  # Не блокируем суперпользователей
        is_staff=False,  # Не блокируем сотрудников
    )

    count = inactive_users.count()

    if count > 0:
        # Обновляем всех найденных пользователей одним запросом
        updated_count = inactive_users.update(is_active=False)
        return f"Blocked {updated_count} inactive users (inactive for more than {days} days)"

    return f"No inactive users found (threshold: {days} days)"


@shared_task
def send_welcome_email(user_id):
    """
    Задача для отправки приветственного письма новому пользователю
    """
    try:
        user = User.objects.get(id=user_id)
        subject = "Добро пожаловать в LMS!"
        message = (
            f"Здравствуйте, {user.first_name or user.email}!\n\n"
            f"Благодарим за регистрацию в нашей образовательной системе.\n"
            f"Теперь вы можете начать обучение на наших курсах.\n\n"
            f"С уважением,\n"
            f"Команда LMS"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return f"Welcome email sent to {user.email}"
    except User.DoesNotExist:
        return f"User with id {user_id} not found"
    except Exception as e:
        return f"Error sending welcome email: {str(e)}"
