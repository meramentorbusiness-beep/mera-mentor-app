import { useAuth } from "@/App";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useEffect } from "react";

export default function Login() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const ref = params.get("ref");
    if (ref) localStorage.setItem("referral_code", ref);
    if (user) navigate("/dashboard", { replace: true });
  }, [user, navigate, location]);

  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center relative overflow-hidden">
      <div className="absolute inset-0 header-texture" />
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-indigo-600/8 rounded-full blur-[120px] -translate-x-1/3 -translate-y-1/3" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-amber-500/8 rounded-full blur-[100px] translate-x-1/3 translate-y-1/3" />

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600 mb-5 shadow-lg shadow-indigo-600/25">
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
          <h1 className="font-heading text-4xl md:text-5xl font-bold text-white tracking-tight mb-2">
            Mera Mentor
          </h1>
          <p className="text-slate-400 text-base font-body mb-1">
            Seekho. Sikhao. Kamao.
          </p>
          <p className="text-amber-400/80 text-sm font-body">
            Learn. Teach. Earn up to <span className="font-semibold text-amber-400">40% commission</span>
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-[0_20px_60px_rgba(0,0,0,0.3)] p-8 animate-slide-up">
          <h2 className="font-heading text-xl font-semibold text-slate-900 mb-1">Welcome back</h2>
          <p className="text-slate-500 font-body text-sm mb-7">Sign in to start learning & earning</p>

          <Button
            data-testid="google-login-btn"
            onClick={handleGoogleLogin}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-6 rounded-xl shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98] text-base"
          >
            <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
              <path fill="#fff" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/>
              <path fill="#fff" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#fff" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#fff" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </Button>

          <div className="mt-7 pt-5 border-t border-slate-100">
            <h3 className="font-heading font-semibold text-slate-800 text-sm mb-4">How Mera Mentor works</h3>
            <div className="space-y-3">
              {[
                { num: "1", text: "Sign up & explore premium courses", icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" },
                { num: "2", text: "Share your unique referral link with learners", icon: "M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" },
                { num: "3", text: "Earn 40% commission on every course purchase", icon: "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" },
              ].map((step) => (
                <div key={step.num} className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-50 text-indigo-600 text-xs font-bold flex items-center justify-center font-number">
                    {step.num}
                  </span>
                  <p className="text-sm text-slate-600 font-body leading-relaxed">{step.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <p className="text-center text-slate-500 text-xs mt-5 font-body">
          7-level deep referral chain with commissions on every renewal
        </p>
      </div>
    </div>
  );
}
