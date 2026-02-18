import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Gift, X, Sparkles, Download } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function Upsell() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [upsell, setUpsell] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(false);

  useEffect(() => {
    const fetchUpsell = async () => {
      try {
        const res = await axios.get(`${API}/courses/${courseId}/upsell`);
        setUpsell(res.data);
      } catch (e) { console.error(e); }
      setLoading(false);
    };
    fetchUpsell();
  }, [courseId]);

  const handleUpsellPurchase = async () => {
    if (!upsell) return;
    setPurchasing(true);
    try {
      const orderRes = await axios.post(`${API}/payments/create-order`, { course_id: upsell.course_id }, { withCredentials: true });
      const order = orderRes.data;
      await axios.post(`${API}/payments/verify`, { order_id: order.order_id, course_id: upsell.course_id, is_upsell: true }, { withCredentials: true });
      toast.success(`Bundle purchased! You saved ${fmt(upsell.original_price - upsell.price)}`);
      navigate("/courses");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Purchase failed");
    } finally { setPurchasing(false); }
  };

  const fmt = (val) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(val);

  if (loading) return <div className="flex items-center justify-center py-20"><div className="loader"></div></div>;
  if (!upsell) { navigate("/courses", { replace: true }); return null; }

  const savings = upsell.original_price - upsell.price;
  const savingsPercent = Math.round((savings / upsell.original_price) * 100);

  return (
    <div className="animate-slide-up max-w-xl mx-auto py-4" data-testid="upsell-page">
      <div className="flex justify-end mb-3">
        <button data-testid="skip-upsell-btn" onClick={() => navigate("/courses")} className="text-slate-400 hover:text-slate-600 p-1.5" aria-label="Skip">
          <X className="w-5 h-5" />
        </button>
      </div>
      <Card className="bg-white rounded-2xl border border-slate-100 shadow-[0_16px_50px_rgb(0,0,0,0.06)] overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 px-6 py-5 text-center relative overflow-hidden">
          <div className="absolute inset-0 header-texture" />
          <div className="relative z-10">
            <div className="inline-flex items-center gap-1.5 bg-white/20 text-white text-xs font-medium px-3 py-1 rounded-full mb-2"><Sparkles className="w-3.5 h-3.5" /> Special Offer</div>
            <h2 className="font-heading text-xl md:text-2xl font-bold text-white mb-0.5">Upgrade Your Learning</h2>
            <p className="text-indigo-200 font-body text-xs">Unlock the complete bundle at an exclusive price</p>
          </div>
        </div>
        <div className="p-6">
          <div className="relative h-40 rounded-xl overflow-hidden mb-5">
            <img src={upsell.image} alt={upsell.title} className="w-full h-full object-cover" />
            <Badge className="absolute top-2.5 left-2.5 bg-amber-500 text-white border-0 font-number font-bold px-2.5 py-0.5 rounded-full text-xs">SAVE {savingsPercent}%</Badge>
          </div>
          <h3 className="font-heading text-lg font-bold text-slate-900 mb-1">{upsell.title}</h3>
          <p className="text-slate-400 font-body text-xs mb-5 leading-relaxed">{upsell.description}</p>
          <div className="bg-slate-50 rounded-xl p-4 mb-5">
            <div className="flex justify-between mb-1.5"><span className="text-slate-400 font-body text-xs">Original</span><span className="font-number text-slate-400 line-through text-sm">{fmt(upsell.original_price)}</span></div>
            <div className="flex justify-between mb-1.5"><span className="text-slate-500 font-body text-xs">Your Price</span><span className="font-number text-xl font-extrabold text-slate-900">{fmt(upsell.price)}</span></div>
            <div className="flex justify-between pt-1.5 border-t border-slate-200"><span className="text-emerald-600 font-body text-xs font-medium">You Save</span><span className="font-number text-emerald-600 font-bold text-sm">{fmt(savings)}</span></div>
          </div>
          <Button data-testid="accept-upsell-btn" onClick={handleUpsellPurchase} disabled={purchasing}
            className="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-5 rounded-full shadow-lg shadow-amber-500/20 transition-all active:scale-[0.98] text-sm">
            {purchasing ? "Processing..." : <><Gift className="w-4 h-4 mr-2" /> Yes, Upgrade Now!</>}
          </Button>
          <button data-testid="decline-upsell-btn" onClick={() => navigate("/courses")} className="w-full text-center text-xs text-slate-400 hover:text-slate-600 py-2 mt-2 font-body">
            No thanks, I'll pass
          </button>
        </div>
      </Card>
    </div>
  );
}
