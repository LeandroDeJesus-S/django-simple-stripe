# Django Simple Stripe

Um package python para facilitar a integração entre [Stripe](https://stripe.com/) com o [Django](https://www.djangoproject.com/).

🚧 Projeto em estágio inicial de desenvolvimento 🔨

### Exemplos de uso
#### Checkout sessions
```py
class MyCheckoutSessionView(StripeCheckoutSessionView):
    ui_mode = 'hosted' # hosted / embedded

    def get_line_items(self, **kwargs) -> list[dict[str, Any]]:
        kwargs.update({
            'price_data': {
                'product_data': {
                    'name': 'product test',
                    'description': 'the product test description',
                },
                'unit_amount': 1000,
                'currency': self.get_currency()
            },
            'quantity': 1,
        })
        return super().get_line_items(**kwargs)
    
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)
```

#### Payment Intents
```py
class MyCheckoutPaymentIntentView(StripePaymentIntentView):
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
```
