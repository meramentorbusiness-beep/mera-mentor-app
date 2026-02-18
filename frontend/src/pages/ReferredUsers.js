import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { ChevronDown, ChevronUp, User, Phone, Mail, ShoppingBag, IndianRupee } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

export default function ReferredUsers() {
  const { user } = useAuth();
  const [counts, setCounts] = useState({ pending: 0, active: 0, churned: 0, total: 0 });
  const [referredUsers, setReferredUsers] = useState([]);
  const [activeTab, setActiveTab] = useState("pending");
  const [expandedUser, setExpandedUser] = useState(null);

  useEffect(() => {
    fetchCounts();
  }, []);

  useEffect(() => {
    fetchUsers(activeTab);
  }, [activeTab]);

  const fetchCounts = async () => {
    try {
      const res = await axios.get(`${API}/referrals/counts`, { withCredentials: true });
      setCounts(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchUsers = async (status) => {
    try {
      const res = await axios.get(`${API}/referrals/users?status=${status}`, { withCredentials: true });
      setReferredUsers(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const formatCurrency = (val) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(val);

  const statusConfig = {
    pending: { label: "Pending", color: "bg-amber-100 text-amber-700", desc: "Signed up but haven't purchased a course yet." },
    active: { label: "Active", color: "bg-emerald-100 text-emerald-700", desc: "Purchased a course and actively learning." },
    churned: { label: "Churned", color: "bg-red-100 text-red-700", desc: "Cancelled or requested refund." },
  };

  const tabDescriptions = {
    pending: "Pending referrals are users you've invited using your referral link but who haven't purchased a course yet. You'll earn your referral reward only when they make a purchase.",
    active: "Active referrals have purchased at least one course. You're earning commissions from their purchases and any future renewals.",
    churned: "Churned referrals have cancelled their subscription or requested a refund. No further commissions will be earned from them.",
  };

  return (
    <div className="animate-slide-up" data-testid="referred-users-page">
      <div className="mb-6">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-1">
          Creators Referred ({counts.total})
        </h1>
        <p className="text-slate-500 font-body">Track your referral network and their activity</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-slate-100/50 p-1 rounded-full inline-flex mb-6" data-testid="referral-tabs">
          <TabsTrigger
            value="pending"
            data-testid="tab-pending"
            className="rounded-full px-5 py-2 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm transition-all font-body text-sm"
          >
            Pending ({counts.pending})
          </TabsTrigger>
          <TabsTrigger
            value="active"
            data-testid="tab-active"
            className="rounded-full px-5 py-2 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm transition-all font-body text-sm"
          >
            Active ({counts.active})
          </TabsTrigger>
          <TabsTrigger
            value="churned"
            data-testid="tab-churned"
            className="rounded-full px-5 py-2 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm transition-all font-body text-sm"
          >
            Churned ({counts.churned})
          </TabsTrigger>
        </TabsList>

        {["pending", "active", "churned"].map((tab) => (
          <TabsContent key={tab} value={tab}>
            {/* Info box */}
            <Card className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6 animate-slide-up">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-full bg-amber-200 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-amber-700 text-xs font-bold">i</span>
                </div>
                <p className="text-sm text-amber-800 font-body leading-relaxed">{tabDescriptions[tab]}</p>
              </div>
            </Card>

            {/* User list */}
            {referredUsers.length === 0 ? (
              <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-12 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto mb-4 flex items-center justify-center">
                  <User className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-slate-500 font-body">No {tab} referrals yet</p>
                <p className="text-sm text-slate-400 font-body mt-1">Share your referral link to get started</p>
              </Card>
            ) : (
              <div className="space-y-3">
                {referredUsers.map((refUser, idx) => (
                  <Collapsible
                    key={refUser.user_id}
                    open={expandedUser === refUser.user_id}
                    onOpenChange={(open) => setExpandedUser(open ? refUser.user_id : null)}
                  >
                    <Card
                      className={`bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden animate-slide-up animate-slide-up-${Math.min(idx + 1, 4)}`}
                      data-testid={`referred-user-card-${idx}`}
                    >
                      <CollapsibleTrigger className="w-full p-4 flex items-center gap-4 hover:bg-slate-50 transition-colors cursor-pointer">
                        {/* Avatar */}
                        <div className="w-11 h-11 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                          <span className="text-slate-600 font-bold font-heading text-sm">
                            {refUser.name?.[0]?.toUpperCase() || "?"}
                          </span>
                        </div>
                        {/* Info */}
                        <div className="flex-1 text-left min-w-0">
                          <p className="font-heading font-semibold text-slate-900 text-sm truncate">{refUser.name || "Unknown"}</p>
                          <p className="text-xs text-slate-500 font-body truncate">
                            {refUser.phone && <span>{refUser.phone} | </span>}
                            {refUser.email}
                          </p>
                        </div>
                        {/* Status badge */}
                        <Badge className={`${statusConfig[refUser.status || "pending"]?.color} text-xs font-medium px-2.5 py-0.5 rounded-full border-0`}>
                          {statusConfig[refUser.status || "pending"]?.label}
                        </Badge>
                        {/* Expand icon */}
                        {expandedUser === refUser.user_id ? (
                          <ChevronUp className="w-5 h-5 text-slate-400 shrink-0" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-slate-400 shrink-0" />
                        )}
                      </CollapsibleTrigger>

                      <CollapsibleContent>
                        <div className="px-4 pb-4 pt-2 border-t border-slate-100">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            {/* Purchases */}
                            <div>
                              <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 font-body flex items-center gap-1.5">
                                <ShoppingBag className="w-3.5 h-3.5" /> Purchases
                              </h4>
                              {refUser.purchases?.length > 0 ? (
                                <div className="space-y-2">
                                  {refUser.purchases.map((p, pi) => (
                                    <div key={pi} className="text-sm bg-slate-50 rounded-lg p-2.5">
                                      <p className="font-medium text-slate-800 font-body">{p.course_title}</p>
                                      <p className="text-xs text-slate-500 font-number">{new Date(p.created_at).toLocaleDateString("en-IN")}</p>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-slate-400 font-body">No purchases yet</p>
                              )}
                            </div>
                            {/* Commissions */}
                            <div>
                              <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2 font-body flex items-center gap-1.5">
                                <IndianRupee className="w-3.5 h-3.5" /> Commission Earned
                              </h4>
                              <div className="bg-emerald-50 rounded-lg p-3">
                                <p className="font-number text-2xl font-extrabold text-emerald-700">
                                  {formatCurrency(refUser.total_commission || 0)}
                                </p>
                                <p className="text-xs text-emerald-600 font-body mt-1">
                                  From {refUser.commissions?.length || 0} transaction(s)
                                </p>
                              </div>
                            </div>
                          </div>
                          {/* Joined date */}
                          <p className="text-xs text-slate-400 mt-3 font-body">
                            Joined: {refUser.created_at ? new Date(refUser.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" }) : "N/A"}
                          </p>
                        </div>
                      </CollapsibleContent>
                    </Card>
                  </Collapsible>
                ))}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
