const stripe = Stripe(document.querySelector('#payment-form').dataset.public);
document.querySelector('#submit').addEventListener('click', confirmPayment);
// let elements


async function initialize(checkoutUrl) {
    showSpinner(true);
    
    const response = await fetch(checkoutUrl, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken')}
    });

    const { clientSecret, appearance } = await response.json();

    elements = stripe.elements({appearance, clientSecret})
    const paymentElement = elements.create('payment', {layout: 'accordion'});
    paymentElement.mount('#payment-element');
    
    showSpinner(false);
}


async function confirmPayment(event) {
    event.preventDefault();
    showSpinner(true);

    const { error } = await stripe.confirmPayment(({
        elements,
        confirmParams: {
            return_url: 'http://localhost:8000/checkout/return/',
        }
    }));
    
    if (error.message) {
        alert(error.message);
    }

    showSpinner(false);
}