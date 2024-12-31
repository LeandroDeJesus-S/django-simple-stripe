const stripe = Stripe(document.forms['paymentForm'].dataset.public);

async function initialize(chekcoutUrl) {
    const fetchClientSecret = async () => {
        const response = await fetch(chekcoutUrl, {
            method: "POST",
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        const { clientSecret } = await response.json();
        return clientSecret;
    };

    const checkout = await stripe.initEmbeddedCheckout({fetchClientSecret,});

    document.querySelector('#checkout-line-items').remove()
    
    checkout.mount('#checkout');
}