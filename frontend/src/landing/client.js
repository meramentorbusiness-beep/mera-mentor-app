export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
export const isInAppBrowser = () => /Instagram|FBAN|FBAV/i.test(navigator.userAgent);
const browser = /Instagram/i.test(navigator.userAgent) ? 'instagram' : /FBAN|FBAV/i.test(navigator.userAgent) ? 'facebook' : 'browser';
const params = new URLSearchParams(window.location.search);
const storage = {
  get(key) { try { return localStorage.getItem(key); } catch { return null; } },
  set(key, value) { try { localStorage.setItem(key, value); return true; } catch { return false; } },
};
const validRef = value => value && /^[\w-]{1,100}$/.test(value);
if (validRef(params.get('ref'))) {
  const saved = storage.set('referral_code', params.get('ref'));
  // In-app browsers must retain ref in the URL: their native "Open in Browser"
  // menu cannot transfer sandboxed localStorage to Chrome/Safari.
  if (saved && !isInAppBrowser()) {
    const cleanUrl = new URL(window.location.href);
    cleanUrl.searchParams.delete('ref');
    window.history.replaceState(window.history.state, '', `${cleanUrl.pathname}${cleanUrl.search}${cleanUrl.hash}`);
  }
}
const uuid = () => crypto.randomUUID();
const isUuid = value => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value || '');
export const visitorId = isUuid(params.get('visitor')) ? params.get('visitor') : storage.get('mm_visitor') || uuid();
storage.set('mm_visitor', visitorId);
export const browserType = ['instagram', 'facebook'].includes(params.get('source_browser')) ? params.get('source_browser') : browser;
export const referralCode = () => validRef(params.get('ref')) ? params.get('ref') : storage.get('referral_code');

export async function api(path, options = {}) {
  const response = await fetch(`${API}${path}`, { credentials: 'include', ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers } });
  let body;
  try { body = await response.json(); } catch { throw new Error('Connection unavailable. Please try again shortly.'); }
  if (!response.ok) {
    const message = typeof body.detail === 'string' ? body.detail : 'Please check your details and try again.';
    const error = new Error(message); error.status = response.status; throw error;
  }
  return body;
}
export function track(event, section = '', value = null) {
  fetch(`${API}/landing/events`, { method: 'POST', keepalive: true, headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ event_id: uuid(), visitor_id: visitorId, event, browser_type: browserType,
      referral_code: referralCode(), section, value }) }).catch(() => {});
}
export function webinarLink(url) {
  const link = new URL(url || process.env.REACT_APP_WEBINAR_URL);
  if (referralCode()) link.searchParams.set('ref', referralCode());
  link.searchParams.set('utm_source', browserType === 'browser' ? 'mera_mentor' : browserType);
  link.searchParams.set('utm_campaign', 'data_analytics');
  return link.href;
}
export function browserLink() {
  const link = new URL(window.location.href);
  if (referralCode()) link.searchParams.set('ref', referralCode());
  link.searchParams.set('visitor', visitorId);
  link.searchParams.set('source_browser', browserType);
  return link.href;
}
export function googleLogin(intent = 'signup') {
  track('signup_started', intent);
  const query = new URLSearchParams({ visitor_id: visitorId, browser_type: browserType, intent });
  if (referralCode()) query.set('ref', referralCode());
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  window.location.assign(`${API}/auth/google/login?${query}`);
}

let checkoutScript;
export function loadCheckout() {
  if (window.Razorpay) return Promise.resolve();
  if (!checkoutScript) checkoutScript = new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'; script.async = true;
    script.onload = resolve;
    script.onerror = () => { checkoutScript = null; script.remove(); reject(new Error('Payment window could not load. Please try again.')); };
    document.body.appendChild(script);
  });
  return checkoutScript;
}