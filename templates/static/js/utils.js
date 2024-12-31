function getCookie(name) {
	const cookies = Object.fromEntries(
		document.cookie.split("; ").map((cookie) => cookie.split("="))
	);

	if (cookies.hasOwnProperty(name)) {
		return cookies[name];
	}
}


function showSpinner(show) {
	const spinnerElement = document.querySelector('#spinner');
	const paymentButtonElement = document.querySelector('#payNowButton');

	if (show) {
		paymentButtonElement.disabled = true;
		spinnerElement.style.display = 'inline-block';
		paymentButtonElement.style.opacity = .5;
	} else {
		paymentButtonElement.disabled = false;
		spinnerElement.style.display = 'none';
		paymentButtonElement.style.opacity = 1;
	}
}