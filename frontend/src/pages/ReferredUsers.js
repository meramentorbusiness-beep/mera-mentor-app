import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { ChevronDown, ChevronUp, User, ShoppingBag, IndianRupee } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";

export default function ReferredUsers() {
  const [counts, setCounts] = useState({ pending: 0, active: 0, churned: 0, total: 0 });
  const [referredUsers, setReferredUsers] = useState([]);
  const [activeTab, setActiveTab] = useState("pending");
  const [expandedUser, setExpandedUser] = useState(null);

  useEffect(() => { fetchCounts(); }, []);
  useEffect(() => { fetchUsers(activeTab); }, [activeTab]);

  const fetchCounts = async () => {
    try { const res = await axios.get(`${API}/referrals/counts`, { withCredentials: true }); setCounts(res.data); } catch (e) { console.error(e); }
  };
  const fetchUsers = async (status) => {
    try { const res = await axios.get(`${API}/referrals/users?status=${status}`, { withCredentials: true }); setReferredUsers(res.data); } catch (e) { console.error(e); }
  };

  const fmt = (val) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(val);

  const statusConfig = {
    pending: { label: "Pending", color: "bg-amber-100 text-amber-700" },
    active: { label: "Active", color: "bg-emerald-100 text-emerald-700" },
    churned: { label: "Churned", color: "bg-red-100 text-red-700" },
  };

  const tabDescriptions = {
    pending: "Pending referrals have signed up using your link but haven't purchased a course yet. You'll earn when they buy. For better conversion, personally reach out to them!",
    active: "Active referrals have purchased at least one course. You're earning commissions from their purchases and future renewals.",
    churned: "Churned referrals have cancelled or requested refunds. No further commissions from them.",
  };

  return (
    <div className="animate-slide-up" data-testid="referred-users-page">
      <div className="mb-5">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Learners Referred ({counts.total})</h1>
        <p className="text-slate-400 font-body text-sm">Track your referral network</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-100/60 p-1 rounded-full inline-flex mb-5" data-testid="referral-tabs">
          {["pending", "active", "churned"].map((tab) => (
            <TabsTrigger key={tab} value={tab} data-testid={`tab-${tab}`}
              className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium capitalize">
              {tab} ({counts[tab]})
            </TabsTrigger>
          ))}
        </TabsList>

        {["pending", "active", "churned"].map((tab) => (
          <TabsContent key={tab} value={tab}>
            <Card className="bg-amber-50/80 border border-amber-200/60 rounded-xl p-3.5 mb-5">
              <div className="flex items-start gap-2.5">
                <div className="w-5 h-5 rounded-full bg-amber-200 flex items-center justify-center shrink-0 mt-0.5">
                  <span className="text-amber-700 text-[10px] font-bold">i</span>
                </div>
                <p className="text-xs text-amber-800 font-body leading-relaxed">{tabDescriptions[tab]}</p>
              </div>
            </Card>

            {referredUsers.length === 0 ? (
              <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center">
                <div className="w-14 h-14 rounded-full bg-slate-100 mx-auto mb-3 flex items-center justify-center">
                  <User className="w-7 h-7 text-slate-400" />
                </div>
                <p className="text-slate-500 font-body text-sm">No {tab} referrals yet</p>
                <p className="text-xs text-slate-400 font-body mt-1">Share your referral link to get started</p>
              </Card>
            ) : (
              <div className="space-y-2">
                {referredUsers.map((refUser, idx) => (
                  <Collapsible key={refUser.user_id} open={expandedUser === refUser.user_id} onOpenChange={(open) => setExpandedUser(open ? refUser.user_id : null)}>
                    <Card className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden" data-testid={`referred-user-card-${idx}`}>
                      <CollapsibleTrigger className="w-full p-3.5 flex items-center gap-3 hover:bg-slate-50/50 transition-colors cursor-pointer">
                        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
                          <span className="text-slate-600 font-bold font-heading text-xs">{refUser.name?.[0]?.toUpperCase() || "?"}</span>
                        </div>
                        <div className="flex-1 text-left min-w-0">
                          <p className="font-heading font-semibold text-slate-900 text-sm truncate">{refUser.name || "Unknown"}</p>
                          <p className="text-[11px] text-slate-400 font-body truncate">{refUser.phone && `${refUser.phone} | `}{refUser.email}</p>
                        </div>
                        <Badge className={`${statusConfig[refUser.status || "pending"]?.color} text-[10px] font-medium px-2 py-0.5 rounded-full border-0`}>
                          {statusConfig[refUser.status || "pending"]?.label}
                        </Badge>
                        {expandedUser === refUser.user_id ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                      </CollapsibleTrigger>
                      <CollapsibleContent>
                        <div className="px-3.5 pb-3.5 pt-1.5 border-t border-slate-100">
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <h4 className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mb-1.5 font-body flex items-center gap-1"><ShoppingBag className="w-3 h-3" /> Purchases</h4>
                              {refUser.purchases?.length > 0 ? (
                                <div className="space-y-1.5">{refUser.purchases.map((p, pi) => (
                                  <div key={pi} className="text-xs bg-slate-50 rounded-lg p-2">
                                    <p className="font-medium text-slate-700">{p.course_title}</p>
                                    <p className="text-[10px] text-slate-400 font-number">{new Date(p.created_at).toLocaleDateString("en-IN")}</p>
                                  </div>
                                ))}</div>
                              ) : <p className="text-xs text-slate-400">No purchases yet</p>}
                            </div>
                            <div>
                              <h4 className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mb-1.5 font-body flex items-center gap-1"><IndianRupee className="w-3 h-3" /> Commission Earned</h4>
                              <div className="bg-emerald-50 rounded-lg p-2.5">
                                <p className="font-number text-xl font-extrabold text-emerald-700">{fmt(refUser.total_commission || 0)}</p>
                                <p className="text-[10px] text-emerald-600 font-body mt-0.5">From {refUser.commissions?.length || 0} transaction(s)</p>
                              </div>
                            </div>
                          </div>
                          <p className="text-[10px] text-slate-400 mt-2 font-body">Joined: {refUser.created_at ? new Date(refUser.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" }) : "N/A"}</p>
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
