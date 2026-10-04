let checkoutScript;

// Load the provider only when a visitor actually initiates checkout.
export function loadCheckout() {
  if (window.Razorpay) return Promise.resolve();
  if (!checkoutScript) checkoutScript = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = resolve;
    script.onerror = () => {
      checkoutScript = null;
      script.remove();
      reject(new Error('Payment window could not load. Please try again.'));
    };
    document.body.appendChild(script);
  });
  return checkoutScript;
}