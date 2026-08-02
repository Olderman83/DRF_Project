import re
from rest_framework import serializers


def validate_youtube_url(value):
    """
    Валидатор для проверки, что ссылка ведет на youtube.com
    """
    # Регулярное выражение для проверки youtube ссылок
    youtube_pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'

    if not re.match(youtube_pattern, value):
        raise serializers.ValidationError(
            "Разрешены только ссылки на youtube.com"
        )
    return value


class YouTubeValidator:
    """
    Класс-валидатор для проверки youtube ссылок
    """

    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        # Получаем значение поля
        video_url = value.get(self.field)

        if video_url:
            youtube_pattern = r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$'
            if not re.match(youtube_pattern, video_url):
                raise serializers.ValidationError(
                    {self.field: "Разрешены только ссылки на youtube.com"}
                )
        return value
