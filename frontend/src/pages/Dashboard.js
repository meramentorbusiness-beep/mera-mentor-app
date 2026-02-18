import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { QRCodeSVG } from "qrcode.react";
import { Copy, Mail, Share2, Download, ChevronDown, ChevronUp, Users, TrendingUp, IndianRupee, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ earned_today: 0, earned_week: 0, earned_lifetime: 0, total_referred: 0 });
  const [showQR, setShowQR] = useState(false);
  const [commissionLevels, setCommissionLevels] = useState([]);

  const referralLink = `${window.location.origin}/login?ref=${user?.referral_code || ""}`;

  useEffect(() => {
    fetchStats();
    fetchLevels();
  }, []);

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/referrals/stats`, { withCredentials: true });
      setStats(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchLevels = async () => {
    try {
      const res = await axios.get(`${API}/commission-levels`);
      setCommissionLevels(res.data.levels);
    } catch (e) {
      console.error(e);
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(referralLink);
    toast.success("Referral link copied!");
  };

  const shareVia = (platform) => {
    const text = `Join me on CommissionChain and learn amazing courses! Use my referral link: ${referralLink}`;
    const urls = {
      whatsapp: `https://wa.me/?text=${encodeURIComponent(text)}`,
      telegram: `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent("Check out these amazing courses!")}`,
      twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(referralLink)}`,
      email: `mailto:?subject=${encodeURIComponent("Join CommissionChain - Earn While You Learn!")}&body=${encodeURIComponent(text)}`,
    };
    window.open(urls[platform], "_blank");
  };

  const downloadQR = () => {
    const svg = document.getElementById("qr-code-svg");
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    canvas.width = 300;
    canvas.height = 300;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    img.onload = () => {
      ctx.fillStyle = "white";
      ctx.fillRect(0, 0, 300, 300);
      ctx.drawImage(img, 0, 0, 300, 300);
      const a = document.createElement("a");
      a.download = "referral-qr-code.png";
      a.href = canvas.toDataURL("image/png");
      a.click();
    };
    img.src = "data:image/svg+xml;base64," + btoa(svgData);
  };

  const formatCurrency = (val) => {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(val);
  };

  return (
    <div className="animate-slide-up" data-testid="dashboard-page">
      {/* Header Banner */}
      <div className="relative bg-slate-900 rounded-2xl overflow-hidden mb-8">
        <div className="absolute inset-0 header-texture" />
        <div
          className="absolute inset-0 opacity-20 mix-blend-overlay bg-cover bg-center"
          style={{ backgroundImage: `url(https://images.unsplash.com/photo-1771011726574-60ab6028724a?w=1200)` }}
        />
        <div className="relative z-10 px-6 md:px-10 py-10 md:py-14 text-center">
          {/* User avatar */}
          <div className="flex justify-center mb-4">
            <div className="w-20 h-20 rounded-full border-4 border-white/20 overflow-hidden shadow-lg">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-2xl font-bold font-heading">
                  {user?.name?.[0] || "U"}
                </div>
              )}
            </div>
          </div>
          <h1 className="font-heading text-3xl md:text-4xl font-bold text-white mb-2">Referral Program</h1>
          <p className="text-slate-300 font-body text-base md:text-lg">
            Earn cash rewards for every successful referral
          </p>

          {/* Stats cards - overlapping */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-8 -mb-16 relative z-20">
            {[
              { label: "Earned today", value: stats.earned_today, icon: <IndianRupee className="w-5 h-5" /> },
              { label: "Earned in last 7 days", value: stats.earned_week, icon: <TrendingUp className="w-5 h-5" /> },
              { label: "Lifetime earnings", value: stats.earned_lifetime, icon: <TrendingUp className="w-5 h-5" /> },
            ].map((stat, idx) => (
              <Card
                key={idx}
                className={`stat-card bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 text-left animate-slide-up animate-slide-up-${idx + 1}`}
                data-testid={`stat-card-${idx}`}
              >
                <p className="text-sm font-medium text-slate-500 uppercase tracking-wider font-body mb-2">{stat.label}</p>
                <p className="font-number text-3xl font-extrabold tracking-tight text-slate-900">
                  {formatCurrency(stat.value)}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Spacer for overlapping cards */}
      <div className="h-12" />

      {/* Referral Link Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 md:p-8 animate-slide-up animate-slide-up-2">
            <div className="flex items-center gap-2 mb-6">
              <div className="h-px flex-1 bg-slate-200" />
              <h2 className="font-heading text-base font-semibold text-slate-600 whitespace-nowrap">Your referral code & link</h2>
              <div className="h-px flex-1 bg-slate-200" />
            </div>

            {/* Referral link input */}
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl p-3 mb-5">
              <input
                data-testid="referral-link-input"
                type="text"
                readOnly
                value={referralLink}
                className="flex-1 bg-transparent text-sm text-slate-700 font-body outline-none truncate"
              />
              <Button
                data-testid="copy-referral-link-btn"
                onClick={copyLink}
                variant="secondary"
                className="bg-slate-900 hover:bg-slate-800 text-white rounded-lg px-5 py-2 text-sm font-semibold shrink-0"
              >
                <Copy className="w-4 h-4 mr-1.5" /> Copy
              </Button>
            </div>

            {/* Share options */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                data-testid="share-email-btn"
                onClick={() => shareVia("email")}
                className="share-btn inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 text-sm font-medium font-body"
              >
                <Mail className="w-4 h-4" /> Invite via Email
              </button>
              <span className="text-slate-300">|</span>
              <button
                data-testid="download-qr-btn"
                onClick={() => setShowQR(!showQR)}
                className="share-btn inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-700 text-sm font-medium font-body"
              >
                <Download className="w-4 h-4" /> {showQR ? "Hide" : "Download"} QR Code
              </button>
              <div className="flex-1" />
              {/* Social icons */}
              <div className="flex items-center gap-2">
                <button data-testid="share-facebook-btn" onClick={() => shareVia("facebook")} className="share-btn w-9 h-9 rounded-full bg-[#1877F2] flex items-center justify-center text-white hover:opacity-90" aria-label="Share on Facebook">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                </button>
                <button data-testid="share-twitter-btn" onClick={() => shareVia("twitter")} className="share-btn w-9 h-9 rounded-full bg-black flex items-center justify-center text-white hover:opacity-90" aria-label="Share on X">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </button>
                <button data-testid="share-telegram-btn" onClick={() => shareVia("telegram")} className="share-btn w-9 h-9 rounded-full bg-[#0088cc] flex items-center justify-center text-white hover:opacity-90" aria-label="Share on Telegram">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                </button>
                <button data-testid="share-whatsapp-btn" onClick={() => shareVia("whatsapp")} className="share-btn w-9 h-9 rounded-full bg-[#25D366] flex items-center justify-center text-white hover:opacity-90" aria-label="Share on WhatsApp">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413z"/></svg>
                </button>
              </div>
            </div>

            {/* QR Code section */}
            {showQR && (
              <div className="mt-6 pt-6 border-t border-slate-100 flex flex-col items-center animate-slide-up">
                <QRCodeSVG id="qr-code-svg" value={referralLink} size={200} level="H" includeMargin />
                <Button data-testid="download-qr-png-btn" onClick={downloadQR} className="mt-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-6" size="sm">
                  <Download className="w-4 h-4 mr-1.5" /> Download PNG
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* How it works sidebar */}
        <div className="lg:col-span-1">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 md:p-8 h-full animate-slide-up animate-slide-up-3">
            <h2 className="font-heading text-lg font-semibold text-slate-900 mb-6">How Referral works</h2>
            <div className="space-y-6">
              {[
                { num: "1", title: "Share your link", desc: "Send your unique referral link to friends." },
                { num: "2", title: "Friend joins & buys", desc: "Anyone who uses your link to sign up and purchase a course becomes your referral." },
                { num: "3", title: "You earn 40% — every time", desc: "Get 40% of their course price, on every purchase and renewal." },
              ].map((step, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <span className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-50 text-indigo-600 text-sm font-bold flex items-center justify-center font-number">
                    {step.num}
                  </span>
                  <div>
                    <h3 className="font-heading font-semibold text-slate-800 text-sm mb-1">{step.title}</h3>
                    <p className="text-sm text-slate-500 font-body leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Commission levels */}
            <div className="mt-8 pt-6 border-t border-slate-100">
              <h3 className="font-heading font-semibold text-slate-800 text-sm mb-3">Commission Levels</h3>
              <div className="space-y-2">
                {commissionLevels.map((l) => (
                  <div key={l.level} className="flex items-center justify-between text-sm">
                    <span className="text-slate-500 font-body">Level {l.level}</span>
                    <span className="font-number font-bold text-amber-600">{l.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 animate-slide-up animate-slide-up-3">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center">
              <Users className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 font-body">Creators Referred</p>
              <p className="font-number text-2xl font-extrabold text-slate-900">{stats.total_referred}</p>
            </div>
          </div>
        </Card>
        <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 animate-slide-up animate-slide-up-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
              <IndianRupee className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-slate-500 font-body">Your Referral Code</p>
              <p className="font-number text-lg font-bold text-slate-900">{user?.referral_code}</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
