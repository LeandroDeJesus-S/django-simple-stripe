from django.urls import path
from . import views

urlpatterns = [
    path('', views.TestStripeCheckoutViews.as_view(), name='checkout'),
    path('success/', views.checkout_session_success_view, name='checkout_session_success'),
    path('cancel/', views.checkout_session_cancel_view, name='checkout_session_cancel'),
    path('return/', views.checkout_session_return_view, name='checkout_session_return'),
    path('webhook/', views.StripeWebHookView.as_view(), name='stripe_webhook'),
]
