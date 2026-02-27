import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { Copy, Mail, Download, Users, IndianRupee, ChevronRight, BookOpen, Play, Award, Flame } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Link } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_earned: 0, this_month: 0, total_referrals: 0 });
  const [showQR, setShowQR] = useState(false);
  const [commissionLevels, setCommissionLevels] = useState([]);
  const [continueLearning, setContinueLearning] = useState([]);
  const [earningsChart, setEarningsChart] = useState([]);
  const [levelChart, setLevelChart] = useState([]);
  const [certificates, setCertificates] = useState([]);
  const [myRank, setMyRank] = useState(null);

  const referralLink = `${window.location.origin}/login?ref=${user?.referral_code || ""}`;

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/referrals/stats`, { withCredentials: true }).then(r => setStats(r.data)).catch(() => {}),
      axios.get(`${API}/commission-levels`).then(r => setCommissionLevels(r.data.levels)).catch(() => {}),
      axios.get(`${API}/progress/continue`, { withCredentials: true }).then(r => setContinueLearning(r.data)).catch(() => {}),
      axios.get(`${API}/analytics/earnings`, { withCredentials: true }).then(r => setEarningsChart(r.data)).catch(() => {}),
      axios.get(`${API}/analytics/commission-by-level`, { withCredentials: true }).then(r => setLevelChart(r.data)).catch(() => {}),
      axios.get(`${API}/certificates`, { withCredentials: true }).then(r => setCertificates(r.data)).catch(() => {}),
      axios.get(`${API}/leaderboard/my-rank`, { withCredentials: true }).then(r => setMyRank(r.data)).catch(() => {}),
    ]);
  }, []);

  const copyLink = () => { navigator.clipboard.writeText(referralLink); toast.success("Referral link copied!"); };
  const shareVia = (p) => {
    const text = `Join me on Mera Mentor! Learn amazing courses and earn by referring. ${referralLink}`;
    const urls = { whatsapp: `https://wa.me/?text=${encodeURIComponent(text)}`, telegram: `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent("Mera Mentor - Learn & Earn!")}`, twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(referralLink)}`, email: `mailto:?subject=${encodeURIComponent("Join Mera Mentor")}&body=${encodeURIComponent(text)}` };
    window.open(urls[p], "_blank");
  };
  const downloadQR = () => {
    const svg = document.getElementById("qr-code-svg");
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas"); canvas.width = 300; canvas.height = 300;
    const ctx = canvas.getContext("2d"); const img = new Image();
    img.onload = () => { ctx.fillStyle = "white"; ctx.fillRect(0, 0, 300, 300); ctx.drawImage(img, 0, 0, 300, 300); const a = document.createElement("a"); a.download = "referral-qr.png"; a.href = canvas.toDataURL("image/png"); a.click(); };
    img.src = "data:image/svg+xml;base64," + btoa(svgData);
  };

  const fmt = (v) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);
  const maxBar = commissionLevels.length > 0 ? commissionLevels[0].percentage : 40;
  const pieColors = ["#4f46e5", "#7c3aed", "#a855f7", "#d946ef", "#ec4899", "#f43f5e", "#f97316"];

  return (
    <div className="animate-slide-up" data-testid="dashboard-page">
      {/* Header Banner */}
      <div className="relative bg-slate-900 rounded-2xl overflow-hidden mb-8">
        <div className="absolute inset-0 header-texture" />
        <div className="absolute inset-0 opacity-15 mix-blend-overlay bg-cover bg-center" style={{ backgroundImage: `url(https://images.unsplash.com/photo-1771011726574-60ab6028724a?w=1200)` }} />
        <div className="relative z-10 px-6 md:px-10 py-8 md:py-10 text-center">
          <div className="flex justify-center mb-3">
            <div className="w-14 h-14 rounded-full border-[3px] border-white/20 overflow-hidden shadow-lg">
              {user?.picture ? <img src={user.picture} alt={user.name} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-lg font-bold">{user?.name?.[0]}</div>}
            </div>
          </div>
          <p className="text-white/50 text-[10px] uppercase tracking-widest mb-0.5">Welcome back</p>
          <h1 className="font-heading text-xl md:text-2xl font-bold text-white mb-0.5">{user?.name}</h1>
          <div className="flex items-center justify-center gap-3 mt-1">
            {myRank?.streak > 0 && <span className="text-orange-400 text-xs font-number">🔥 {myRank.streak} day streak</span>}
            {myRank?.xp > 0 && <span className="text-indigo-300 text-xs font-number">{myRank.xp} XP</span>}
            {myRank?.badge !== "none" && myRank?.badge && <span className="text-amber-400 text-xs capitalize font-body">{myRank.badge}</span>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-6 -mb-12 relative z-20">
            {[{ label: "Earned today", value: stats.total_earned || 0 }, { label: "This month", value: stats.this_month || 0 }, { label: "Lifetime", value: stats.total_earned || 0 }].map((s, i) => (
              <Card key={i} className={`stat-card bg-white rounded-xl border-0 shadow-[0_8px_30px_rgb(0,0,0,0.06)] p-4 text-left animate-slide-up animate-slide-up-${i + 1}`} data-testid={`stat-card-${i}`}>
                <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mb-1">{s.label}</p>
                <p className="font-number text-xl md:text-2xl font-extrabold text-slate-900">{fmt(s.value)}</p>
              </Card>
            ))}
          </div>
        </div>
      </div>
      <div className="h-8" />

      {/* Continue Learning */}
      {continueLearning.length > 0 && (
        <div className="mb-6">
          <h2 className="font-heading text-base font-semibold text-slate-900 mb-3">Continue Learning</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {continueLearning.map((c) => (
              <Link key={c.course_id} to={`/courses/${c.course_id}`}>
                <Card className="stat-card bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-3 cursor-pointer" data-testid={`continue-${c.course_id}`}>
                  <img src={c.image} alt={c.course_title} className="w-14 h-10 rounded-lg object-cover shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-slate-800 truncate font-heading">{c.course_title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Progress value={c.progress_pct} className="h-1.5 flex-1" />
                      <span className="text-[10px] font-number text-slate-400">{c.progress_pct}%</span>
                    </div>
                    {c.next_lesson && <p className="text-[10px] text-indigo-500 mt-0.5 truncate flex items-center gap-0.5"><Play className="w-2.5 h-2.5" />{c.next_lesson.title}</p>}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Charts + Referral Link */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-6">
        {/* Earnings Chart */}
        <div className="lg:col-span-3">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 animate-slide-up animate-slide-up-1">
            <h2 className="font-heading text-sm font-semibold text-slate-900 mb-4">Earnings (Last 30 Days)</h2>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={earningsChart}>
                  <XAxis dataKey="date" tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} interval={4} />
                  <YAxis tick={{ fontSize: 9, fill: "#94a3b8" }} tickLine={false} axisLine={false} width={40} tickFormatter={(v) => `₹${v}`} />
                  <Tooltip formatter={(v) => [`₹${v}`, "Earned"]} contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Line type="monotone" dataKey="amount" stroke="#4f46e5" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        {/* Commission by Level Pie */}
        <div className="lg:col-span-2">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 animate-slide-up animate-slide-up-2">
            <h2 className="font-heading text-sm font-semibold text-slate-900 mb-3">Commission by Level</h2>
            {levelChart.length > 0 ? (
              <div className="flex items-center gap-4">
                <div className="w-32 h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={levelChart} dataKey="total" nameKey="level" cx="50%" cy="50%" innerRadius={25} outerRadius={50} paddingAngle={2}>
                        {levelChart.map((_, i) => <Cell key={i} fill={pieColors[i % pieColors.length]} />)}
                      </Pie>
                      <Tooltip formatter={(v) => [`₹${v}`]} contentStyle={{ fontSize: 10, borderRadius: 8 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="space-y-1 flex-1">
                  {levelChart.map((l, i) => (
                    <div key={l.level} className="flex items-center gap-2 text-[10px]">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: pieColors[i] }} />
                      <span className="text-slate-500">L{l.level}</span>
                      <span className="font-number font-bold text-slate-700 ml-auto">{fmt(l.total)}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 text-center py-6">No commission data yet</p>
            )}
          </Card>
        </div>
      </div>

      {/* Referral Link + Commission Structure */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 mb-6">
        <div className="lg:col-span-3">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 animate-slide-up animate-slide-up-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="h-px flex-1 bg-slate-200" /><h2 className="font-heading text-xs font-semibold text-slate-500">Your referral link</h2><div className="h-px flex-1 bg-slate-200" />
            </div>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl p-2 mb-3">
              <input data-testid="referral-link-input" type="text" readOnly value={referralLink} className="flex-1 bg-transparent text-xs text-slate-600 outline-none truncate px-2" />
              <Button data-testid="copy-referral-link-btn" onClick={copyLink} className="bg-slate-900 hover:bg-slate-800 text-white rounded-lg px-3 py-1.5 text-[10px] font-semibold shrink-0"><Copy className="w-3 h-3 mr-1" />Copy</Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button data-testid="share-email-btn" onClick={() => shareVia("email")} className="share-btn text-indigo-600 text-[10px] font-medium flex items-center gap-1"><Mail className="w-3 h-3" />Email</button>
              <span className="text-slate-200">|</span>
              <button data-testid="download-qr-btn" onClick={() => setShowQR(!showQR)} className="share-btn text-indigo-600 text-[10px] font-medium flex items-center gap-1"><Download className="w-3 h-3" />QR</button>
              <div className="flex-1" />
              {[{ id: "facebook", c: "#1877F2", p: "M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" }, { id: "twitter", c: "#000", p: "M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" }, { id: "telegram", c: "#0088cc", p: "M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" }, { id: "whatsapp", c: "#25D366", p: "M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z" }].map(s => (
                <button key={s.id} data-testid={`share-${s.id}-btn`} onClick={() => shareVia(s.id)} className="share-btn w-7 h-7 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: s.c }} aria-label={s.id}>
                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24"><path d={s.p}/></svg>
                </button>
              ))}
            </div>
            {showQR && (
              <div className="mt-4 pt-4 border-t border-slate-100 flex flex-col items-center animate-slide-up">
                <QRCodeSVG id="qr-code-svg" value={referralLink} size={160} level="H" includeMargin />
                <Button data-testid="download-qr-png-btn" onClick={downloadQR} className="mt-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-4 text-[10px]" size="sm"><Download className="w-3 h-3 mr-1" />PNG</Button>
              </div>
            )}
          </Card>
        </div>

        {/* Commission Pyramid */}
        <div className="lg:col-span-2">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5 h-full animate-slide-up animate-slide-up-3">
            <h2 className="font-heading text-sm font-semibold text-slate-900 mb-1">Commission Structure</h2>
            <p className="text-[10px] text-slate-400 mb-4">Earn on 5 levels deep</p>
            <div className="space-y-2">
              {commissionLevels.map((l, i) => {
                const w = (l.percentage / maxBar) * 100;
                const colors = ["bg-indigo-600", "bg-violet-500", "bg-purple-500", "bg-fuchsia-500", "bg-pink-500"];
                return (
                  <div key={l.level}>
                    <div className="flex justify-between mb-0.5">
                      <span className="text-[10px] text-slate-500">{i === 0 ? "Direct" : `Level ${l.level}`}</span>
                      <span className="font-number text-[10px] font-bold text-slate-600">{fmt(l.example_earning)} <span className="text-slate-400">({l.percentage}%)</span></span>
                    </div>
                    <div className="h-5 bg-slate-100 rounded-full overflow-hidden">
                      <div className={`commission-level-bar h-full ${colors[i]} rounded-full flex items-center justify-end pr-1.5`} style={{ width: `${w}%` }}>
                        <span className="text-[8px] text-white font-bold font-number">{fmt(l.example_earning)}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg p-3">
              <p className="text-[10px] text-slate-600 mb-2 font-medium">💰 Your earning potential on {fmt(799)} course:</p>
              <div className="grid grid-cols-2 gap-1 text-[10px]">
                <div><span className="text-slate-500">L1 (5 people):</span> <span className="font-number font-bold text-indigo-600">{fmt(5 * 319.60)}</span></div>
                <div><span className="text-slate-500">L2 (25):</span> <span className="font-number font-bold text-indigo-600">{fmt(25 * 95.88)}</span></div>
                <div><span className="text-slate-500">L3 (125):</span> <span className="font-number font-bold text-indigo-600">{fmt(125 * 47.94)}</span></div>
                <div><span className="text-slate-500">L4 (625):</span> <span className="font-number font-bold text-indigo-600">{fmt(625 * 23.97)}</span></div>
              </div>
              <p className="text-[11px] text-indigo-700 font-bold mt-2">Total: {fmt(50000)}+ 🔥</p>
            </div>
          </Card>
        </div>
      </div>

      {/* Certificates + Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link to="/referrals">
          <Card className="stat-card bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-3 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center"><Users className="w-4 h-4 text-indigo-600" /></div>
            <div className="flex-1"><p className="text-[10px] text-slate-400">Learners Referred</p><p className="font-number text-lg font-extrabold text-slate-900">{stats.total_referred}</p></div>
            <ChevronRight className="w-4 h-4 text-slate-300" />
          </Card>
        </Link>
        <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center"><Award className="w-4 h-4 text-amber-600" /></div>
          <div><p className="text-[10px] text-slate-400">Certificates</p><p className="font-number text-lg font-extrabold text-slate-900">{certificates.length}</p></div>
        </Card>
        <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center"><IndianRupee className="w-4 h-4 text-purple-600" /></div>
          <div><p className="text-[10px] text-slate-400">Referral Code</p><p className="font-number text-sm font-bold text-slate-900">{user?.referral_code}</p></div>
        </Card>
      </div>
    </div>
  );
}
