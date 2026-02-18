import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Gift, ArrowRight, X, IndianRupee, Star, Sparkles } from "lucide-react";
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
    fetchUpsell();
  }, [courseId]);

  const fetchUpsell = async () => {
    try {
      const res = await axios.get(`${API}/courses/${courseId}/upsell`);
      setUpsell(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpsellPurchase = async () => {
    if (!upsell) return;
    setPurchasing(true);
    try {
      await axios.post(`${API}/purchases`, { course_id: upsell.course_id, is_upsell: true }, { withCredentials: true });
      toast.success(`Bundle purchased! You saved ${formatCurrency(upsell.original_price - upsell.price)}`);
      navigate("/courses");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Purchase failed");
    } finally {
      setPurchasing(false);
    }
  };

  const formatCurrency = (val) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(val);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!upsell) {
    // No upsell available, redirect to courses
    navigate("/courses", { replace: true });
    return null;
  }

  const savings = upsell.original_price - upsell.price;
  const savingsPercent = Math.round((savings / upsell.original_price) * 100);

  return (
    <div className="animate-slide-up max-w-2xl mx-auto" data-testid="upsell-page">
      {/* Close button */}
      <div className="flex justify-end mb-4">
        <button
          data-testid="skip-upsell-btn"
          onClick={() => navigate("/courses")}
          className="text-slate-400 hover:text-slate-600 transition-colors p-2"
          aria-label="Skip offer"
        >
          <X className="w-6 h-6" />
        </button>
      </div>

      {/* Upsell card */}
      <Card className="bg-white rounded-2xl border border-slate-100 shadow-[0_20px_60px_rgb(0,0,0,0.08)] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 px-8 py-6 text-center relative overflow-hidden">
          <div className="absolute inset-0 header-texture" />
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 bg-white/20 text-white text-sm font-medium px-4 py-1.5 rounded-full mb-3 font-body">
              <Sparkles className="w-4 h-4" /> Special Offer — Limited Time
            </div>
            <h2 className="font-heading text-2xl md:text-3xl font-bold text-white mb-1">Upgrade Your Learning</h2>
            <p className="text-indigo-200 font-body text-sm">Unlock the complete bundle at an exclusive price</p>
          </div>
        </div>

        {/* Body */}
        <div className="p-8">
          {/* Course image */}
          <div className="relative h-48 rounded-xl overflow-hidden mb-6">
            <img src={upsell.image} alt={upsell.title} className="w-full h-full object-cover" />
            <Badge className="absolute top-3 left-3 bg-amber-500 text-white border-0 font-number font-bold px-3 py-1 rounded-full text-sm">
              SAVE {savingsPercent}%
            </Badge>
          </div>

          <h3 className="font-heading text-xl font-bold text-slate-900 mb-2">{upsell.title}</h3>
          <p className="text-slate-500 font-body text-sm mb-6 leading-relaxed">{upsell.description}</p>

          {/* Pricing */}
          <div className="bg-slate-50 rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 font-body text-sm">Original Price</span>
              <span className="font-number text-slate-400 line-through">{formatCurrency(upsell.original_price)}</span>
            </div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-slate-500 font-body text-sm">Your Special Price</span>
              <span className="font-number text-2xl font-extrabold text-slate-900">{formatCurrency(upsell.price)}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-slate-200">
              <span className="text-emerald-600 font-body text-sm font-medium">You Save</span>
              <span className="font-number text-emerald-600 font-bold">{formatCurrency(savings)}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3">
            <Button
              data-testid="accept-upsell-btn"
              onClick={handleUpsellPurchase}
              disabled={purchasing}
              className="w-full bg-amber-500 hover:bg-amber-600 text-white font-bold py-6 rounded-full shadow-lg shadow-amber-500/20 transition-all active:scale-[0.98] text-base"
            >
              {purchasing ? (
                "Processing..."
              ) : (
                <>
                  <Gift className="w-5 h-5 mr-2" /> Yes, Upgrade Now!
                </>
              )}
            </Button>
            <button
              data-testid="decline-upsell-btn"
              onClick={() => navigate("/courses")}
              className="w-full text-center text-sm text-slate-400 hover:text-slate-600 py-2 font-body transition-colors"
            >
              No thanks, I'll pass on this deal
            </button>
          </div>
        </div>
      </Card>
    </div>
  );
}
