class StripeCustomCheckoutHandler extends IPaymentProviderHandler {
	_confirmPayment(elements, return_url) {
		const inner = async (e) => {
			const { error } = await this._provider.confirmPayment(({
				elements,
				confirmParams: {
					return_url,
				},
			}));

			if (error.message) {
				console.log(error)
				alert(error.message);
			}
		};
		return inner;
	}

	async _initialize(csrfToken, checkoutUrl, layout, paymentElementSelector) {
		const response = await fetch(checkoutUrl, {
			method: "POST",
			headers: { "X-CSRFToken": csrfToken },
		});

		const { clientSecret, appearance } = await response.json();

		const elements = this._provider.elements({ appearance, clientSecret });
		const paymentElement = elements.create("payment", {layout: layout});
		paymentElement.mount(paymentElementSelector);
		return elements;
	}

	async handle(settings) {
		const {
			csrfToken,
			checkoutUrl,
			layout,
			paymentElementSelector,
			confirmPaymentElementSelector,
			returnUrl,
		} = settings;

		const elements = await this._initialize(
			csrfToken,
			checkoutUrl,
			layout,
			paymentElementSelector
		);
		document
			.querySelector(confirmPaymentElementSelector)
			.addEventListener(
				"click",
				this._confirmPayment(elements, returnUrl)
			);
	}
}

class StripeCheckoutEmbeddedHandler extends IPaymentProviderHandler {
	_fetchClientSecret(csrfToken, checkoutUrl) {
		const inner = async (e) => {
			const response = await fetch(checkoutUrl, {
				method: "POST",
				headers: {
					"X-CSRFToken": csrfToken,
				},
			});
			const { clientSecret } = await response.json();
			return clientSecret;
		};
		return inner;
	}

	async handle(settings) {
		const { checkoutUrl, csrfToken, checkoutElementSelector, confirmationBtnSelector } = settings;
		document.querySelector(confirmationBtnSelector).addEventListener('click', async () => {
			document.querySelector(checkoutElementSelector).innerHTML = '';
			const checkout = await this._provider.initEmbeddedCheckout({
				fetchClientSecret: this._fetchClientSecret(csrfToken, checkoutUrl),
			});
			checkout.mount(checkoutElementSelector);
		})
	}
}

class StripeCheckoutHostedHandler extends IPaymentProviderHandler {
    handle(settings) {
		const confirmationBtn = document.querySelector(settings.confirmationBtnSelector);
		confirmationBtn.addEventListener('click', async () => {
			const response = await fetch(settings.checkoutUrl, {
				method: "POST",
				headers: {
					"X-CSRFToken": settings.csrfToken,
				},
			});
			const { checkoutSessionURL } = await response.json();
			location.replace(checkoutSessionURL);
		})
    }
}
