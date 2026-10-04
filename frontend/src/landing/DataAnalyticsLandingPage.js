import { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, BarChart3, ExternalLink, Instagram, Mail, MessageCircle, ShieldCheck } from 'lucide-react';
import { api, isInAppBrowser, track, googleLogin, loadCheckout, visitorId, browserType, referralCode } from './client';
import { Hero, CourseStack, Curriculum, Reviews, Instructor, Pricing, FAQ, WebinarButton } from './Sections';
import { SalaryCalculator, ReferralCalculator } from './Calculators';
import { BrowserDialog, LegalDialog } from './Dialogs';
import { LearningPromise } from './LearningPromise';
import { AccountButton } from './AccountButton';
import './landing.css';

export default function DataAnalyticsLandingPage() {
  const [data, setData] = useState(null);
  const [contentError, setContentError] = useState(false);
  const [browserOpen, setBrowserOpen] = useState(false);
  const [legal, setLegal] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [scrolled, setScrolled] = useState(false);
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const viewed = useRef(false);
  const resumed = useRef(false);
  const inApp = isInAppBrowser();
  const settings = data?.settings;

  useEffect(() => {
    document.title = 'Data Analytics in 2 Months — No Coding Background Needed | Mera Mentor';
    api('/landing/data-analytics').then(setData).catch(() => setContentError(true));
    let active = true;
    // Use the existing server-verified Google session, never a localStorage identity.
    api('/auth/me').then(account => { if (active) setUser(account); })
      .catch(() => { if (active) setUser(null); })
      .finally(() => { if (active) setCheckingSession(false); });
    if (!viewed.current) { viewed.current = true; track('page_view'); }
    const onScroll = () => setScrolled(window.scrollY > 420);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    const authError = new URLSearchParams(window.location.search).get('auth_error');
    if (authError) setNotice('Google sign-in complete nahi hua. Dobara try karein, ya free webinar join karein.');
    return () => { active = false; window.removeEventListener('scroll', onScroll); };
  }, []);

  const openBrowser = () => { track('browser_open', 'signup'); setBrowserOpen(true); };
  const signup = () => {
    if (checkingSession) return;
    if (user) { window.location.assign('/dashboard'); return; }
    if (inApp) return openBrowser();
    if (data && !data.google_ready) return setNotice('Google sign-in is temporarily unavailable. Aap free webinar directly join kar sakte hain.');
    googleLogin('signup');
  };

  const buy = async source => {
    track('course_click', source);
    if (inApp) return openBrowser();
    if (!data?.checkout_ready) {
      setNotice(contentError ? 'Course details unavailable. Please try again shortly.' : 'Enrollment is not open yet. Free webinar join karein; course access publish hone par enrollment available hoga.');
      document.getElementById('signup')?.scrollIntoView({ behavior: 'smooth' }); return;
    }
    if (busy) return;
    setBusy(true); setNotice('');
    try {
      let current = user;
      if (!current) {
        try { current = await api('/auth/me'); setUser(current); }
        catch (error) { if (error.status === 401) { googleLogin('purchase'); return; } throw error; }
      }
      await loadCheckout();
      const order = await api('/payments/create-order', { method: 'POST', body: JSON.stringify({ course_id: settings.course_id, referral_code: referralCode(), visitor_id: visitorId, browser_type: browserType }) });
      const checkout = new window.Razorpay({ key: order.key_id, amount: order.amount_paise, currency: order.currency, order_id: order.order_id,
        name: 'Mera Mentor', description: 'Data Analytics Career Course', prefill: { name: current.name, email: current.email }, theme: { color: '#ff7029' },
        handler: async result => {
          try {
            const verified = await api('/payments/verify', { method: 'POST', body: JSON.stringify({ ...result, visitor_id: visitorId, browser_type: browserType }) });
            setNotice('Payment verified. Aapka course ready hai!');
            window.location.assign(`/courses/${encodeURIComponent(verified.course_id || settings.course_id)}`);
          } catch (error) { setNotice(error.message); } finally { setBusy(false); }
        }, modal: { ondismiss: () => { setBusy(false); setNotice('Payment cancelled. Aap jab ready ho, tab continue karein.'); } } });
      checkout.on('payment.failed', () => { setBusy(false); setNotice('Payment failed. No course access was granted. Please try again.'); });
      checkout.open();
    } catch (error) { setBusy(false); setNotice(error.message); }
  };

  useEffect(() => {
    if (data?.checkout_ready && !resumed.current && new URLSearchParams(window.location.search).get('checkout') === '1') {
      resumed.current = true;
      buy('oauth-return');
    }
  });

  return <div className="lp" data-testid="data-analytics-landing">
    {inApp && <div className="lp-webview-banner" data-testid="instagram-webview-banner"><span>📱 Best experience ke liye tap karein ⋮ → Open in Browser</span><button data-testid="banner-open-browser" onClick={openBrowser} aria-label="Open in Browser"><ExternalLink size={18} /></button></div>}
    <header className="lp-header"><div className="lp-wrap"><a className="lp-brand" href="/courses/data-analytics" aria-label="Mera Mentor home" data-testid="landing-brand"><span className="lp-brand-icon"><BarChart3 size={24} /></span><span>mera<span className="lp-orange">mentor</span><small>SEEKHO. SIKHAO. KAMAO.</small></span></a><nav aria-label="Course navigation"><a href="#course" data-testid="nav-course">The course</a><a href="#curriculum" data-testid="nav-curriculum">Curriculum</a><a href="#reviews" data-testid="nav-reviews">Reviews</a><a href="#faq" data-testid="nav-faq">FAQs</a></nav><AccountButton user={user} inApp={inApp} checking={checkingSession} onSignIn={signup} compact /></div></header>
    <main>
      <Hero webinarUrl={data?.webinar_url} />
      <CourseStack />
      <LearningPromise webinarUrl={data?.webinar_url} />
      <SalaryCalculator />
      <ReferralCalculator />
      <Curriculum />
      <Reviews reviews={data?.reviews} loading={!data && !contentError} error={contentError} />
      <Instructor settings={settings} />
      <Pricing settings={settings} onBuy={buy} busy={busy} paymentMode={data?.payment_mode} />
      <FAQ experience={settings?.instructor_experience} />
      <section className="lp-section lp-final" id="signup"><div className="lp-wrap"><span className="lp-eyebrow">YOUR FUTURE SELF WILL THANK YOU.</span><h2 className="lp-heading">Scrolling se aage badho.<br /><span>Apni story badlo.</span></h2><p>Pehla step free hai. Bas shuru toh karo.</p><div className="lp-final-actions"><WebinarButton source="final" url={data?.webinar_url}>Free Webinar</WebinarButton><button className="lp-button lp-button-outline" data-testid="buy-course-final" disabled={busy} onClick={() => buy('final')}>Buy Course ₹1,299<ArrowRight size={19} /></button></div><div className="lp-signup"><span>{user ? `Welcome back, ${user.name || 'learner'}.` : 'Your courses. Your progress. One dashboard.'}</span><AccountButton user={user} inApp={inApp} checking={checkingSession} onSignIn={signup} /><span className="lp-signup-note"><ShieldCheck size={16} />{user ? 'Your existing account and learning progress stay together.' : 'Secure Google sign-in. No payment needed to create an account.'}</span></div>{notice && <div className="lp-notice" role="status" data-testid="landing-notice">{notice}</div>}</div></section>
    </main>
    <footer className="lp-footer"><div className="lp-wrap"><div className="lp-footer-main"><div><a href="/courses/data-analytics" className="lp-brand" data-testid="footer-brand"><span className="lp-brand-icon"><BarChart3 size={24} /></span><span>mera<span className="lp-orange">mentor</span></span></a><p>Skills that open doors.<br />A community that has your back.</p></div><div className="lp-footer-links"><span>LET’S TALK</span><a href={`mailto:${settings?.support_email || 'Nikhilparwani205@gmail.com'}`} data-testid="footer-support"><Mail size={18} />Contact support<ArrowUpRight size={16} /></a>{settings?.whatsapp_number && <a href={`https://wa.me/${settings.whatsapp_number.replace(/\D/g, '')}`} target="_blank" rel="noopener noreferrer" data-testid="footer-whatsapp"><MessageCircle size={18} />WhatsApp us<ArrowUpRight size={16} /></a>}<div className="lp-socials">{settings?.instagram_url && <a href={settings.instagram_url} data-testid="footer-instagram" target="_blank" rel="noopener noreferrer" aria-label="Instagram"><Instagram size={23} /></a>}{settings?.linkedin_url && <a href={settings.linkedin_url} data-testid="footer-linkedin" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn"><b>in</b></a>}</div></div></div><div className="lp-footer-bottom"><span>© {new Date().getFullYear()} Mera Mentor. All rights reserved.</span><div><button data-testid="footer-terms" onClick={() => setLegal('terms')}>Terms & conditions</button><button data-testid="footer-privacy" onClick={() => setLegal('privacy')}>Privacy policy</button></div><span>Made for your next chapter. ↗</span></div></div></footer>
    <div className={`lp-sticky-cta ${scrolled ? 'lp-sticky-visible' : ''}`} data-testid="sticky-cta-bar" aria-hidden={!scrolled} inert={!scrolled ? true : undefined}><div className="lp-wrap"><div className="lp-sticky-label"><strong>Your next chapter. Just ₹1,299.</strong><span>Lifetime access · Beginner friendly</span></div><WebinarButton source="sticky" url={data?.webinar_url} className="lp-button-outline">Free Webinar</WebinarButton><button className="lp-button" data-testid="buy-course-sticky" disabled={busy} onClick={() => buy('sticky')}>Buy Course ₹1,299<ArrowUpRight size={18} /></button></div></div>
    <BrowserDialog open={browserOpen} onClose={() => setBrowserOpen(false)} />
    <LegalDialog type={legal} onClose={() => setLegal(null)} email={settings?.support_email || 'Nikhilparwani205@gmail.com'} />
  </div>;
}