import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { ShoppingCart, Star, Tag, IndianRupee, Check } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function Courses() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [purchasing, setPurchasing] = useState(null);

  useEffect(() => {
    fetchCourses();
    fetchPurchases();
  }, []);

  const fetchCourses = async () => {
    try {
      const res = await axios.get(`${API}/courses`);
      setCourses(res.data.filter((c) => !c.is_upsell));
    } catch (e) {
      console.error(e);
    }
  };

  const fetchPurchases = async () => {
    try {
      const res = await axios.get(`${API}/purchases`, { withCredentials: true });
      setPurchases(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const isPurchased = (courseId) => purchases.some((p) => p.course_id === courseId);

  const handlePurchase = async (courseId) => {
    setPurchasing(courseId);
    try {
      const res = await axios.post(`${API}/purchases`, { course_id: courseId }, { withCredentials: true });
      toast.success(`Successfully purchased ${res.data.course_title}!`);
      fetchPurchases();
      // Check for upsell
      navigate(`/upsell/${courseId}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Purchase failed");
    } finally {
      setPurchasing(null);
    }
  };

  const formatCurrency = (val) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(val);

  const discount = (original, current) => Math.round(((original - current) / original) * 100);

  return (
    <div className="animate-slide-up" data-testid="courses-page">
      <div className="mb-8">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-1">Course Marketplace</h1>
        <p className="text-slate-500 font-body">Browse and purchase courses. Your referrals earn you commission on every sale!</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {courses.map((course, idx) => {
          const owned = isPurchased(course.course_id);
          return (
            <Card
              key={course.course_id}
              className={`bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 animate-slide-up animate-slide-up-${Math.min(idx + 1, 4)}`}
              data-testid={`course-card-${idx}`}
            >
              {/* Course Image */}
              <div className="relative h-44 overflow-hidden">
                <img
                  src={course.image}
                  alt={course.title}
                  className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
                />
                {course.original_price && course.original_price > course.price && (
                  <Badge className="absolute top-3 left-3 bg-amber-500 text-white border-0 font-number text-xs px-2 py-0.5 rounded-full">
                    {discount(course.original_price, course.price)}% OFF
                  </Badge>
                )}
                <Badge className="absolute top-3 right-3 bg-white/90 text-slate-700 border-0 text-xs px-2 py-0.5 rounded-full font-body">
                  {course.category}
                </Badge>
              </div>

              {/* Course Info */}
              <div className="p-5">
                <h3 className="font-heading font-semibold text-slate-900 text-base mb-2">{course.title}</h3>
                <p className="text-sm text-slate-500 font-body leading-relaxed mb-4 line-clamp-2">{course.description}</p>

                {/* Price */}
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="font-number text-2xl font-extrabold text-slate-900">{formatCurrency(course.price)}</span>
                  {course.original_price && course.original_price > course.price && (
                    <span className="font-number text-sm text-slate-400 line-through">{formatCurrency(course.original_price)}</span>
                  )}
                </div>

                {/* Action */}
                {owned ? (
                  <Button
                    disabled
                    className="w-full bg-emerald-100 text-emerald-700 font-semibold rounded-full py-5 cursor-default"
                    data-testid={`course-purchased-${idx}`}
                  >
                    <Check className="w-4 h-4 mr-1.5" /> Already Purchased
                  </Button>
                ) : (
                  <Button
                    data-testid={`buy-course-btn-${idx}`}
                    onClick={() => handlePurchase(course.course_id)}
                    disabled={purchasing === course.course_id}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-full py-5 shadow-lg shadow-indigo-500/20 transition-all active:scale-[0.98]"
                  >
                    {purchasing === course.course_id ? (
                      "Processing..."
                    ) : (
                      <>
                        <ShoppingCart className="w-4 h-4 mr-1.5" /> Buy Now
                      </>
                    )}
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
