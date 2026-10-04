import { ArrowUpRight, ExternalLink, LayoutDashboard } from 'lucide-react';

export const AccountButton = ({ user, inApp, checking, onSignIn, compact = false }) => {
  const className = compact ? 'lp-header-cta lp-account-header' : 'lp-google-button';
  const source = compact ? 'header' : 'signup';
  if (user) return <a href="/dashboard" className={className} data-testid={`${source}-dashboard-link`}><LayoutDashboard size={compact ? 18 : 21} /><span>{compact ? 'Dashboard' : 'Go to Dashboard'}</span><ArrowUpRight size={18} /></a>;
  return <button type="button" className={className} disabled={checking} aria-busy={checking} onClick={onSignIn}
    aria-label={inApp ? 'Open in Browser for Google sign-in' : 'Continue with Google to your dashboard'}
    data-testid={compact ? 'header-google-login' : inApp ? 'signup-open-browser' : 'signup-google'}>
    {inApp ? <ExternalLink size={compact ? 18 : 21} /> : <span className="lp-google-g" aria-hidden="true">G</span>}
    <span>{compact ? 'Sign in' : inApp ? 'Open in Browser for Google' : 'Continue with Google'}</span>
    {!compact && <ArrowUpRight size={18} />}
  </button>;
};