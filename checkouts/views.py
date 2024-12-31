import logging
import os
from copy import deepcopy
from hashlib import sha256
from typing import Any, Callable
import re

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import BadRequest
from django.http import HttpRequest, JsonResponse
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from stripe_customers.models import StripeCustomer
from utils.support import get_user_lang

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger("djangoStripe")


class StripeSessionMixin:
    """Mixin class to help configure session-based checkouts
    """
    PAYMENT_MODE = "payment"
    SUBSCRIPTION_MODE = "subscription"
    mode: str = PAYMENT_MODE

    on_creation_fail_url: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None
    return_url: str | None = None

    _protocol = "http://" if settings.DEBUG else "https://"

    def get_on_creation_fail_url(self):
        """url to redirenc if some stripe exception is raised on create session"""
        if self.on_creation_fail_url is None:
            return self.request.META.get("HTTP_REFERER", "/")
        return self.on_creation_fail_url

    def get_success_url(self):
        """url to redict after checkout completed with success"""
        if self.success_url is None:
            return (
                self._protocol
                + self.request.get_host()
                + reverse_lazy("checkout_session_success")
            )
        return self.success_url

    def get_cancel_url(self):
        """url to redict if the checkout was canceled"""
        if self.cancel_url is None:
            return (
                self._protocol
                + self.request.get_host()
                + reverse_lazy("checkout_session_cancel")
            )
        return self.cancel_url

    def get_return_url(self):
        """url to return to after checkout. Regardless of status"""
        if self.return_url is None:
            return (
                self._protocol
                + self.request.get_host()
                + reverse_lazy("checkout_session_return")
                + "?session_id={CHECKOUT_SESSION_ID}"
            )
        return self.return_url

    def get_session_params(self, **extra) -> dict:
        """hook method to setup the stripe session object"""
        return


class StripeAppearanceMixin:
    """Mixin class to help setup the stripe payment object appearance"""
    theme = "stripe"
    labels_style = "floating"

    appearance = {
        "theme": theme,
        "labels": labels_style,
    }

    def get_appearance(self):
        assert isinstance(self.appearance, dict), "The attr `appearance` must be a vaid dict."
        return self.appearance


class StripeBaseCheckoutView(View):
    """base view to the stripe checkout views"""
    template_name: str | None = None
    stipe_public_key: str | None = None
    currency: str | None = None
    default_currency: str = 'usd'
    _currency_mapping: dict = {
        'pt': 'eur',
        'pt-BR': 'brl',
        'en': 'usd',
        'en-US': 'usd',
        'en-GB': 'gbp',
        'es': 'eur',
        'es-ES': 'eur',
        'es-MX': 'mxn',
    }

    def get_currency(self) -> str:
        """return the currency code using the `HTTP_ACCEPT_LANGUAGE` meta value in lower case."""
        if self.currency is None:
            user_lang = get_user_lang(self.request)
            c = self.default_currency if user_lang is None else self._currency_mapping.get(user_lang, self.default_currency)
            return c.lower()
        return self.currency.lower()

    def get_template_name(self) -> str:
        if not self.template_name or not isinstance(self.template_name, str):
            raise ValueError("invalid template name")
        return self.template_name
    
    def _validate_stripe_key(self):
        """verify if the stripe public key is setted in class or in the settings module and
        check if the regex pattern matches"""
        if self.stipe_public_key is None and not hasattr(settings, 'STRIPE_PUBLIC_KEY'):
            raise ValueError('stripe public is not defined')
        
        key = self.stipe_public_key if self.stipe_public_key is not None else settings.STRIPE_PUBLIC_KEY
        assert re.match(r'^pk_(test_)?[A-Za-z0-9]+$', key) is not None, 'invalid stripe public key'
        assert isinstance(key, str), 'the stripe public key must be an valid string'
    
    def get_srtipe_public_key(self) -> str | None:
        self._validate_stripe_key()
        if self.stipe_public_key is None:
            return settings.STRIPE_PUBLIC_KEY
        return self.stipe_public_key

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        kwargs['STRIPE_PUBLIC_KEY'] = self.get_srtipe_public_key()
        return kwargs


class StripeCheckoutSessionView(StripeSessionMixin, StripeBaseCheckoutView):
    _ONEDAY_IN_MIN = 1440
    expire_minutes = 30

    HOSTED_UIMODE = "hosted"
    EMBEDDED_UIMODE = "embedded"
    ui_mode: str = EMBEDDED_UIMODE

    def get_line_items(self, **kwargs) -> list[dict[str, Any]]:
        """hook method to return the line items dict which will be sent to the stripe session"""
        return [kwargs]

    def get_ui_mode(self) -> str:
        """return the checkout session ui mode."""
        valid_modes = [mode for mode in vars(self.__class__).keys() if mode.endswith('_UIMODE')]
        assert self.ui_mode not in valid_modes, f"invalid `ui_mode` param. The valid modes are: {valid_modes}"
        return self.ui_mode

    def get_expires(self) -> int:
        """returns the expiration time of the checkout session"""
        if (
            not isinstance(self.expire_minutes, int)
            or not 30 <= self.expire_minutes <= self._ONEDAY_IN_MIN
        ):
            raise TypeError(
                "`expire_minutes` must be a valid integer between 30 and 1440 (24h)"
            )
        return int(
            (datetime.now() + timedelta(minutes=self.expire_minutes)).timestamp()
        )

    def get_template_name(self) -> str:
        if self.template_name is None:
            templates = {
                self.HOSTED_UIMODE: "checkouts/checkout-hosted.html",
                self.EMBEDDED_UIMODE: "checkouts/checkout-embedded.html",
            }
            return templates[self.get_ui_mode()]
        return self.template_name

    def get_session_params(self, **extra) -> dict:
        """return the stripe session object params"""
        params = {
            'mode': self.mode,
            "ui_mode": self.get_ui_mode(),
            "line_items": self.get_line_items(),
            "expires_at": self.get_expires(),
        }
        ui_mode_params = {
            self.HOSTED_UIMODE: {
                "success_url": self.get_success_url(),
                "cancel_url": self.get_cancel_url(),
            },
            self.EMBEDDED_UIMODE: {
                "return_url": self.get_return_url(),
            }
        }
        params.update(ui_mode_params[self.get_ui_mode()])
        if extra:
            params.update(extra)

        return params

    def create_checkout_sesion(
        self, *args, **kwargs
    ) -> stripe.checkout.Session | HttpResponseRedirect:
        """Creates the stripe checkout session and return.

        Returns:
            stripe.checkout.Session: the stripe checkout session created.
            HttpResponseRedirect: if some fail occur redirect to the on_creation_fail_url attr value. Defaults to http referer or / if no referer found.
        """
        redirect_ = redirect(self.get_on_creation_fail_url())
        session_params = self.get_session_params()

        if self.request.user.is_authenticated:
            customer = StripeCustomer.objects.filter(user=self.request.user).first()
            if customer is not None:
                session_params["customer"] = customer.customer_id
                logger.debug(
                    f"user {str(customer)} was related with the customer id {customer.customer_id} to the session"
                )

        try:
            session = stripe.checkout.Session.create(**session_params)
        except stripe.StripeError as e:
            logger.error(
                f"Error on create session: {str(e)} | session params: {session_params}"
            )
            return redirect_

        logger.info("checkout session created successfully")
        return session

    def get(self, *args, **kwargs):
        context = self.get_context_data()
        template = self.get_template_name()
        logger.debug(f"context data: {context} | template {template}")
        return render(self.request, template, context)

    def post(self, *args, **kwargs):
        checkout_session = self.create_checkout_sesion()
        logger.debug(f"final checkout session object: {checkout_session}")

        if isinstance(checkout_session, HttpResponseRedirect):
            return checkout_session

        ui_mode_responses = {
            self.HOSTED_UIMODE: JsonResponse({'checkoutSessionURL': checkout_session.url}),
            self.EMBEDDED_UIMODE: JsonResponse({"clientSecret": checkout_session.client_secret}),
        }
        response = ui_mode_responses[self.get_ui_mode()]
        logger.info(f"checkout view response: {response}")
        return response


class StripePaymentIntentView(StripeBaseCheckoutView, StripeAppearanceMixin):
    automatic_payment_methods = True
    payment_method_types = []
    default_payment_method_type = "card"
    template_name = "checkouts/checkout-custom.html"

    def get_payment_method_types(self):
        if self.automatic_payment_methods and self.payment_method_types:
            raise ValueError(
                "`automatic_payment_methods` and `payment_method_types` are excludents"
            )

        if not self.payment_method_types:
            return [self.default_payment_method_type]
        return self.payment_method_types

    def set_idempotency_key(self, params, inplace=True) -> dict | None:
        """Convert the params to str and if the user is authenticated appends
        the id and the stripe customer idempotency key from database to the string.
        The resultant string is hashed using sha256 and used as the idempotency key.


        Args:
            params (dict): the payment intent object params.
            inplace (bool, optional): if False returns a copy of the params with the idempotency key. Defaults to True.

        Returns:
            dict | None: the params copy if implace is false
        """
        string = ""
        params_str = str(params)
        if self.request.user.is_authenticated:
            string += str(self.request.user.pk)
            string += str(self.request.user.stripe_customer.idempotency_key)

        string += params_str
        idempotency_key = sha256(string.encode()).hexdigest()
        if inplace:
            params["idempotency_key"] = idempotency_key
            return

        params_copy = deepcopy(params)
        params_copy["idempotency_key"] = idempotency_key
        return params_copy

    def get_payment_intent_params(self, **extra):
        params = {"currency": self.get_currency()}

        if self.automatic_payment_methods:
            params["automatic_payment_methods"] = {
                "enabled": self.automatic_payment_methods
            }
        else:
            params["payment_method_types"] = self.payment_method_types

        if self.request.user.is_authenticated:
            params["customer"] = self.request.user.stripe_customer.customer_id

        params.update(extra)
        return params

    def create_intent(self):
        params = self.get_payment_intent_params()
        self.set_idempotency_key(params)
        return stripe.PaymentIntent.create(**params)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context

    def get(self, *args, **kwargs):
        context = self.get_context_data()
        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        intent = self.create_intent()
        logger.debug(f"payment intent object: {intent}")
        appearance = self.get_appearance()
        logger.debug(f"payment element appearance: {appearance}")

        response = JsonResponse(
            {"clientSecret": intent.client_secret, "appearance": appearance}
        )
        return response


def checkout_session_success_view(request):
    return render(request, "checkouts/success.html")


def checkout_session_cancel_view(request):
    return render(request, "checkouts/cancel.html")


def checkout_session_return_view(request):
    context = {}

    checkout_session_id = request.GET.get("session_id")
    payment_intent_id = request.GET.get("payment_intent")
    payment_intent_client_secret = request.GET.get("payment_intent_client_secret")

    # it's using the stripe checkout session embedded or hosted flow
    if checkout_session_id is not None:
        checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)
        status = checkout_session.status
        if status == "open":
            return redirect("checkout")

        elif status == "complete":
            context["status"] = status
            context["customer_email"] = checkout_session.customer_email
            context["total"] = checkout_session.amount_total
            return render(request, "checkouts/return.html", context)

        elif status == "expired":
            messages.info(request, "session expired.")
            return redirect("checkout")

    # it's using customized flow with stripe payment intents
    elif payment_intent_id is not None and payment_intent_client_secret is not None:
        pi = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["customer"])
        context["status"] = pi.status
        context["customer_email"] = pi.customer.email if pi.customer else ''
        context["total"] = f"{pi.amount / 100:.2f}"
        return render(request, "checkouts/return.html", context)

    messages.info("something went wrong! please, try again.")
    return redirect("checkout")


class StripeWebHookView(View):
    event_dict = {}
    event_callbacks = {
        "customer.created": lambda o: logger.info(f"customer {o.id} created")
    }

    def get_event_dict(self):
        DEFAULT_EVENT_DICT = {
            "checkout.session.async_payment_failed": None,
            "checkout.session.async_payment_succeeded": None,
            "checkout.session.completed": None,
            "checkout.session.expired": None,
            "customer.created": None,
            "customer.deleted": None,
            "payment_intent.amount_capturable_updated": None,
            "payment_intent.canceled": None,
            "payment_intent.created": None,
            "payment_intent.partially_funded": None,
            "payment_intent.payment_failed": None,
            "payment_intent.processing": None,
            "payment_intent.requires_action": None,
            "payment_intent.succeeded": None,
        }
        if self.event_dict:
            return self.event_dict
        return DEFAULT_EVENT_DICT

    def set_event_callbacks(self):
        if not self.event_callbacks:
            return

        self.event_dict.update(self.event_callbacks)

    def post(self, request: HttpRequest, *args, **kwargs):
        event = None
        payload = request.body
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:  # Invalid payload
            logger.error(str(e))
            raise BadRequest

        except stripe.error.SignatureVerificationError as e:
            logger.warning(str(e))
            raise e

        self.event_dict = self.get_event_dict()
        self.set_event_callbacks()

        if event.type not in self.event_dict:
            logger.warning("Unhandled event type {}".format(event["type"]))
            return JsonResponse({"success": False})

        callback_func = self.event_dict[event.type]
        target_object = event.data.object

        if isinstance(callback_func, Callable):
            callback_func(target_object)

        elif isinstance(callback_func, str):
            getattr(self, callback_func)(target_object)

        return JsonResponse({"success": True})

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


# teste
# class TestStripeCheckoutViews(StripeCheckoutSessionView):
#     ui_mode = 'hosted'

#     def get_line_items(self, **kwargs) -> list[dict[str, Any]]:
#         kwargs.update({
#             'price_data': {
#                 'product_data': {
#                     'name': 'product test',
#                     'description': 'the product test description',
#                 },
#                 'unit_amount': 1000,
#                 'currency': self.get_currency()
#             },
#             'quantity': 1,
#         })
#         return super().get_line_items(**kwargs)
    
#     def get(self, *args, **kwargs):
#         return super().get(*args, **kwargs)


class TestStripeCheckoutViews(StripePaymentIntentView):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["product"] = {
            "name": "My very nice product",
            "price": "R$150,00",
            "image": "https://picsum.photos/400/300",
        }
        return ctx

    def get_payment_intent_params(self, **extra):
        params = super().get_payment_intent_params(**extra)

        params["description"] = "some description"
        params["amount"] = 150_00
        return params
