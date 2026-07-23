import stripe
from django.conf import settings
from decimal import Decimal
from django.core.exceptions import ValidationError


class StripeService:
    """
    Сервис для работы с API Stripe
    """

    def __init__(self):
        """
        Инициализация с API ключом из настроек
        """
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_product(self, name, description=None):
        """
        Создание продукта в Stripe

        Args:
            name (str): Название продукта
            description (str, optional): Описание продукта

        Returns:
            dict: Данные созданного продукта
        """
        try:
            product_data = {
                'name': name,
                'active': True,
            }

            if description:
                product_data['description'] = description

            product = stripe.Product.create(**product_data)
            return {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'active': product.active,
                'created': product.created
            }
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания продукта в Stripe: {str(e)}")

    def create_price(self, product_id, amount, currency='usd'):
        """
        Создание цены для продукта в Stripe

        Args:
            product_id (str): ID продукта в Stripe
            amount (Decimal): Сумма в валюте
            currency (str): Валюта (по умолчанию 'usd')

        Returns:
            dict: Данные созданной цены
        """
        try:
            # Конвертируем сумму в копейки (cents)
            amount_in_cents = int(amount * 100)

            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount_in_cents,
                currency=currency,
            )

            return {
                'id': price.id,
                'product': price.product,
                'unit_amount': price.unit_amount,
                'currency': price.currency,
                'created': price.created
            }
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания цены в Stripe: {str(e)}")

    def create_checkout_session(self, price_id, success_url, cancel_url):
        """
        Создание сессии для оплаты в Stripe

        Args:
            price_id (str): ID цены в Stripe
            success_url (str): URL для перенаправления после успешной оплаты
            cancel_url (str): URL для перенаправления при отмене оплаты

        Returns:
            dict: Данные созданной сессии
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
            )

            return {
                'id': session.id,
                'url': session.url,
                'payment_status': session.payment_status,
                'created': session.created,
                'amount_total': session.amount_total,
                'currency': session.currency
            }
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка создания сессии оплаты в Stripe: {str(e)}")

    def retrieve_session(self, session_id):
        """
        Получение информации о сессии

        Args:
            session_id (str): ID сессии в Stripe

        Returns:
            dict: Данные сессии
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'id': session.id,
                'payment_status': session.payment_status,
                'amount_total': session.amount_total,
                'currency': session.currency,
                'customer_email': session.customer_details.email if session.customer_details else None,
                'created': session.created
            }
        except stripe.error.StripeError as e:
            raise ValidationError(f"Ошибка получения сессии из Stripe: {str(e)}")
