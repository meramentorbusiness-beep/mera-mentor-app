import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API } from "@/App";
import axios from "axios";
import { Users, BookOpen, Star, ArrowRight, CheckCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function ReferralLanding() {
  const { code } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API}/referral/${code}`);
        setData(res.data);
        localStorage.setItem("referral_code", code);
      } catch { }
      setLoading(false);
    };
    fetchData();
  }, [code]);

  const handleJoin = () => {
    localStorage.setItem("referral_code", code);
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const fmt = (v) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(v);

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="loader"></div></div>;

  if (!data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Card className="bg-white rounded-xl p-8 text-center max-w-sm mx-4">
          <p className="text-slate-500 mb-4">Invalid referral link</p>
          <Button onClick={() => navigate("/login")} className="rounded-full bg-indigo-600 text-white text-xs">Go to Login</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 relative overflow-hidden" data-testid="referral-landing-page">
      <div className="absolute inset-0 header-texture" />
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] -translate-x-1/3 -translate-y-1/3" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-amber-500/8 rounded-full blur-[100px] translate-x-1/3 translate-y-1/3" />

      <div className="relative z-10 max-w-3xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
            </div>
            <span className="font-heading font-bold text-white text-xl">Mera Mentor</span>
          </div>
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-white mb-3">
            Join under <span className="text-amber-400">{data.referrer?.name}</span>
          </h1>
          <p className="text-slate-400 text-base">and start your learning journey today</p>
        </div>

        {/* Referrer Card */}
        <Card className="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/10 p-6 mb-8 text-center">
          <div className="w-16 h-16 rounded-full mx-auto mb-3 overflow-hidden border-2 border-white/20">
            {data.referrer?.picture ? <img src={data.referrer.picture} alt={data.referrer.name} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-xl font-bold">{data.referrer?.name?.[0]}</div>}
          </div>
          <p className="text-white font-heading font-bold text-lg mb-1">{data.referrer?.name}</p>
          <p className="text-slate-400 text-xs mb-4">invites you to learn & earn</p>

          <div className="flex justify-center gap-8">
            <div><p className="font-number text-2xl font-extrabold text-white">{data.total_students}+</p><p className="text-[10px] text-slate-400">Students</p></div>
            <div><p className="font-number text-2xl font-extrabold text-amber-400">40%</p><p className="text-[10px] text-slate-400">Commission</p></div>
            <div><p className="font-number text-2xl font-extrabold text-white">{data.courses?.length}</p><p className="text-[10px] text-slate-400">Courses</p></div>
          </div>
        </Card>

        {/* Benefits */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[
            { icon: BookOpen, title: "Learn Skills", desc: "Expert-curated courses in tech, marketing & more" },
            { icon: Users, title: "Build Network", desc: "Refer friends and grow your learning community" },
            { icon: Star, title: "Earn Money", desc: "Up to 40% commission on 5 levels deep" },
          ].map((b, i) => (
            <Card key={i} className="bg-white/5 backdrop-blur-sm rounded-xl border border-white/10 p-5 text-center">
              <div className="w-10 h-10 rounded-lg bg-indigo-600/20 flex items-center justify-center mx-auto mb-3">
                <b.icon className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="font-heading font-semibold text-white text-sm mb-1">{b.title}</h3>
              <p className="text-[11px] text-slate-400">{b.desc}</p>
            </Card>
          ))}
        </div>

        {/* Course Preview */}
        {data.courses?.length > 0 && (
          <div className="mb-8">
            <h2 className="font-heading text-lg font-bold text-white mb-4 text-center">Popular Courses</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.courses.slice(0, 3).map((c) => (
                <Card key={c.course_id} className="bg-white rounded-xl overflow-hidden">
                  <img src={c.image} alt={c.title} className="w-full h-32 object-cover" />
                  <div className="p-3">
                    <Badge className="bg-slate-100 text-slate-600 border-0 text-[9px] mb-1">{c.category}</Badge>
                    <h3 className="font-heading font-semibold text-xs text-slate-900 mb-1">{c.title}</h3>
                    <div className="flex items-baseline gap-1.5">
                      <span className="font-number text-base font-extrabold text-slate-900">{fmt(c.price)}</span>
                      {c.original_price > c.price && <span className="font-number text-[10px] text-slate-400 line-through">{fmt(c.original_price)}</span>}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="text-center">
          <Button onClick={handleJoin} className="bg-amber-500 hover:bg-amber-600 text-white font-bold py-6 px-10 rounded-full shadow-lg shadow-amber-500/25 text-base transition-all active:scale-[0.98]" data-testid="join-now-btn">
            Join Now & Start Learning <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
          <p className="text-slate-500 text-[10px] mt-3">Free to join. Buy courses at your own pace.</p>
        </div>
      </div>
    </div>
  );
}
