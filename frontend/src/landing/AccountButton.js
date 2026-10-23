import { ArrowRight, ExternalLink, LayoutDashboard, LogOut } from 'lucide-react';

// "Find Courses" is the landing page's single entry point into the existing Google sign-in.
export const FindCoursesButton = ({ inApp, checking, onClick, source, className = 'lp-button' }) =>
  <button type="button" className={className} disabled={checking} aria-busy={checking} onClick={onClick}
    aria-label={inApp ? 'Find Courses (opens your browser for Google sign-in)' : 'Find Courses'}
    data-testid={`find-courses-${source}`}>
    {inApp && <ExternalLink size={18} />}<span>Find Courses</span><ArrowRight size={18} />
  </button>;

export const AccountButton = ({ user, inApp, checking, onSignIn, onLogout, compact = false }) => {
  const source = compact ? 'header' : 'signup';
  const linkClass = compact ? 'lp-header-cta lp-account-header' : 'lp-google-button';
  if (!user) return <FindCoursesButton inApp={inApp} checking={checking} onClick={onSignIn} source={source} className={compact ? linkClass : 'lp-button'} />;
  const firstName = (user.name || 'My account').split(' ')[0];
  return <div className="lp-account" data-testid={`${source}-account`}>
    <a href="/dashboard" className={linkClass} data-testid={`${source}-dashboard-link`} title={user.email || ''}>
      {user.picture ? <img className="lp-account-avatar" src={user.picture} alt="" width="26" height="26" referrerPolicy="no-referrer" /> : <LayoutDashboard size={compact ? 18 : 21} />}
      <span className="lp-account-name">{compact ? firstName : 'Go to Dashboard'}</span>
    </a>
    <button type="button" className="lp-logout" onClick={onLogout} data-testid={`${source}-logout`} aria-label="Log out"><LogOut size={18} />{!compact && <span>Log out</span>}</button>
  </div>;
};
