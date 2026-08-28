import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { ShoppingCart, Check, Play, BookOpen } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function Courses() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [purchasing, setPurchasing] = useState(null);

  useEffect(() => { fetchCourses(); fetchPurchases(); }, []);

  const fetchCourses = async () => {
    try { const res = await axios.get(`${API}/courses`); setCourses(res.data.filter((c) => !c.is_upsell)); } catch (e) { console.error(e); }
  };
  const fetchPurchases = async () => {
    try { const res = await axios.get(`${API}/purchases`, { withCredentials: true }); setPurchases(res.data); } catch (e) { console.error(e); }
  };

  const isPurchased = (courseId) => purchases.some((p) => p.course_id === courseId);

  const handlePurchase = async (course) => {
    setPurchasing(course.course_id);
    try {
      const orderRes = await axios.post(`${API}/payments/create-order`, { course_id: course.course_id }, { withCredentials: true });
      const order = orderRes.data;

      if (order.key_id) {
        // Real Razorpay checkout
        const options = {
          key: order.key_id,
          amount: order.amount_paise,
          currency: order.currency,
          name: "Mera Mentor",
          description: order.course?.title || course.title,
          order_id: order.order_id,
          handler: async (response) => {
            await axios.post(`${API}/payments/verify`, {
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            }, { withCredentials: true });
            toast.success(`Successfully purchased ${order.course?.title || course.title}!`);
            fetchPurchases();
            navigate(`/upsell/${course.course_id}`);
          },
          prefill: { name: user?.name, email: user?.email },
          theme: { color: "#4F46E5" },
          modal: { ondismiss: () => setPurchasing(null) },
        };
        const rzp = new window.Razorpay(options);
        rzp.open();
        return; // setPurchasing handled by modal ondismiss / handler
      } else {
        // Demo mode — no Razorpay keys configured
        await axios.post(`${API}/payments/verify`, {
          razorpay_order_id: order.order_id,
          razorpay_payment_id: `pay_demo_${Date.now()}`,
          razorpay_signature: "",
        }, { withCredentials: true });
        toast.success(`Successfully purchased ${order.course?.title || course.title}!`);
        fetchPurchases();
        navigate(`/upsell/${course.course_id}`);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Purchase failed");
    } finally {
      setPurchasing(null);
    }
  };

  const fmt = (val) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(val);
  const discount = (orig, cur) => Math.round(((orig - cur) / orig) * 100);

  return (
    <div className="animate-slide-up" data-testid="courses-page">
      <div className="mb-6">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Course Marketplace</h1>
        <p className="text-slate-400 font-body text-sm">Learn from the best. Every purchase you refer earns you commission!</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {courses.map((course, idx) => {
          const owned = isPurchased(course.course_id);
          return (
            <Card key={course.course_id} className={`bg-white rounded-xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] overflow-hidden hover:shadow-[0_8px_30px_rgb(0,0,0,0.07)] transition-all duration-300 animate-slide-up animate-slide-up-${Math.min(idx + 1, 4)}`} data-testid={`course-card-${idx}`}>
              <div className="relative h-40 overflow-hidden">
                <img src={course.image} alt={course.title} className="w-full h-full object-cover transition-transform duration-500 hover:scale-105" />
                {course.original_price && course.original_price > course.price && (
                  <Badge className="absolute top-2.5 left-2.5 bg-amber-500 text-white border-0 font-number text-[10px] px-2 py-0.5 rounded-full">{discount(course.original_price, course.price)}% OFF</Badge>
                )}
                <Badge className="absolute top-2.5 right-2.5 bg-white/90 text-slate-600 border-0 text-[10px] px-2 py-0.5 rounded-full">{course.category}</Badge>
                {course.lesson_count > 0 && (
                  <div className="absolute bottom-2.5 left-2.5 bg-black/60 text-white text-[10px] px-2 py-1 rounded-lg flex items-center gap-1 backdrop-blur-sm">
                    <Play className="w-3 h-3" /> {course.lesson_count} lessons
                  </div>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-heading font-semibold text-slate-900 text-sm mb-1.5">{course.title}</h3>
                <p className="text-xs text-slate-400 font-body leading-relaxed mb-3 line-clamp-2">{course.description}</p>
                <div className="flex items-baseline gap-2 mb-3">
                  <span className="font-number text-xl font-extrabold text-slate-900">{fmt(course.price)}</span>
                  {course.original_price && course.original_price > course.price && (
                    <span className="font-number text-xs text-slate-400 line-through">{fmt(course.original_price)}</span>
                  )}
                </div>
                {owned ? (
                  <div className="flex gap-2">
                    <Button onClick={() => navigate(`/courses/${course.course_id}`)} className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-full py-4 text-xs" data-testid={`view-course-btn-${idx}`}>
                      <BookOpen className="w-3.5 h-3.5 mr-1" /> Start Learning
                    </Button>
                  </div>
                ) : (
                  <Button data-testid={`buy-course-btn-${idx}`} onClick={() => handlePurchase(course)} disabled={purchasing === course.course_id}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-full py-4 shadow-lg shadow-indigo-500/15 transition-all active:scale-[0.98] text-xs">
                    {purchasing === course.course_id ? "Processing..." : <><ShoppingCart className="w-3.5 h-3.5 mr-1" /> Buy Now</>}
                  </Button>
                )}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
