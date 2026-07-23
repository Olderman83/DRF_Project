from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.views.generic import TemplateView

# Настройка schema view для документации
schema_view = get_schema_view(
    openapi.Info(
        title="LMS API Documentation",
        default_version='v1',
        description="Документация API для образовательной платформы",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@lms.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('', admin.site.urls),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/lms/', include('lms.urls')),

    # Payment pages (опционально)
    # path('payment/success/', TemplateView.as_view(template_name='payment_success.html'), name='payment_success'),
    # path('payment/cancel/', TemplateView.as_view(template_name='payment_cancel.html'), name='payment_cancel'),

    # Swagger documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
