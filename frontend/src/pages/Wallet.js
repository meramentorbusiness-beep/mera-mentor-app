import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { IndianRupee, ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, Wallet as WalletIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export default function Wallet() {
  const [wallet, setWallet] = useState({ balance: 0, total_earned: 0, total_withdrawn: 0 });
  const [transactions, setTransactions] = useState({ commissions: [], payouts: [] });
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutOpen, setPayoutOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { fetchWallet(); fetchTransactions(); }, []);

  const fetchWallet = async () => {
    try { const res = await axios.get(`${API}/wallet`, { withCredentials: true }); setWallet(res.data); } catch (e) { console.error(e); }
  };
  const fetchTransactions = async () => {
    try { const res = await axios.get(`${API}/wallet/transactions`, { withCredentials: true }); setTransactions(res.data); } catch (e) { console.error(e); }
  };

  const requestPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) { toast.error("Enter a valid amount"); return; }
    setSubmitting(true);
    try {
      await axios.post(`${API}/wallet/payout`, { amount }, { withCredentials: true });
      toast.success(`Payout of ${fmt(amount)} requested!`);
      setPayoutOpen(false); setPayoutAmount(""); fetchWallet(); fetchTransactions();
    } catch (e) { toast.error(e.response?.data?.detail || "Payout failed"); }
    finally { setSubmitting(false); }
  };

  const fmt = (val) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(val);
  const statusColors = { pending: "bg-amber-100 text-amber-700", approved: "bg-emerald-100 text-emerald-700", paid: "bg-indigo-100 text-indigo-700" };

  return (
    <div className="animate-slide-up" data-testid="wallet-page">
      <div className="mb-5">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Commission Wallet</h1>
        <p className="text-slate-400 font-body text-sm">Track earnings and request payouts</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        {[
          { label: "Available Balance", value: wallet.balance, icon: WalletIcon, color: "bg-emerald-50 text-emerald-600", testId: "wallet-balance" },
          { label: "Total Earned", value: wallet.total_earned, icon: ArrowDownLeft, color: "bg-indigo-50 text-indigo-600", testId: "total-earned" },
          { label: "Total Withdrawn", value: wallet.total_withdrawn, icon: ArrowUpRight, color: "bg-rose-50 text-rose-600", testId: "total-withdrawn" },
        ].map((s, i) => (
          <Card key={i} className={`stat-card bg-white rounded-xl border border-slate-100 shadow-[0_4px_20px_rgb(0,0,0,0.03)] p-5 animate-slide-up animate-slide-up-${i + 1}`}>
            <div className="flex items-center gap-2.5 mb-2.5">
              <div className={`w-9 h-9 rounded-lg ${s.color} flex items-center justify-center`}><s.icon className="w-4 h-4" /></div>
              <p className="text-xs font-medium text-slate-400 font-body">{s.label}</p>
            </div>
            <p className="font-number text-2xl md:text-3xl font-extrabold text-slate-900" data-testid={s.testId}>{fmt(s.value)}</p>
          </Card>
        ))}
      </div>

      <div className="mb-6">
        <Dialog open={payoutOpen} onOpenChange={setPayoutOpen}>
          <DialogTrigger asChild>
            <Button data-testid="request-payout-btn" className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-full shadow-lg shadow-indigo-500/15 text-xs">
              <IndianRupee className="w-3.5 h-3.5 mr-1" /> Request Payout
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle className="font-heading text-lg">Request Payout</DialogTitle>
              <DialogDescription className="font-body text-xs">Available: {fmt(wallet.balance)}. Min: {fmt(100)}</DialogDescription>
            </DialogHeader>
            <div className="py-3">
              <Input data-testid="payout-amount-input" type="number" min="100" max={wallet.balance} value={payoutAmount} onChange={(e) => setPayoutAmount(e.target.value)} placeholder="Enter amount" className="font-number text-base h-11" />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPayoutOpen(false)} className="rounded-full text-xs">Cancel</Button>
              <Button data-testid="confirm-payout-btn" onClick={requestPayout} disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs">
                {submitting ? "Processing..." : "Confirm"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="commissions">
        <TabsList className="bg-slate-100/60 p-1 rounded-full inline-flex mb-5" data-testid="transaction-tabs">
          <TabsTrigger value="commissions" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium">
            Commissions ({transactions.commissions.length})
          </TabsTrigger>
          <TabsTrigger value="payouts" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium">
            Payouts ({transactions.payouts.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="commissions">
          {transactions.commissions.length === 0 ? (
            <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center">
              <p className="text-slate-400 font-body text-sm">No commissions yet. Share your referral link!</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {transactions.commissions.map((c, idx) => (
                <Card key={c.commission_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-3.5 flex items-center gap-3" data-testid={`commission-row-${idx}`}>
                  <div className="w-9 h-9 rounded-full bg-emerald-50 flex items-center justify-center shrink-0"><ArrowDownLeft className="w-4 h-4 text-emerald-600" /></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-xs font-medium text-slate-700 truncate">From {c.from_user_name || "User"}</p>
                    <p className="text-[10px] text-slate-400">{c.course_title} &middot; L{c.level} &middot; {new Date(c.created_at).toLocaleDateString("en-IN")}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-number font-bold text-emerald-600 text-xs">+{fmt(c.amount)}</p>
                    <Badge className={`${statusColors[c.status]} text-[10px] px-1.5 py-0 rounded-full border-0`}>{c.status}</Badge>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="payouts">
          {transactions.payouts.length === 0 ? (
            <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center">
              <p className="text-slate-400 font-body text-sm">No payouts yet.</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {transactions.payouts.map((p, idx) => (
                <Card key={p.payout_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-3.5 flex items-center gap-3" data-testid={`payout-row-${idx}`}>
                  <div className="w-9 h-9 rounded-full bg-rose-50 flex items-center justify-center shrink-0"><ArrowUpRight className="w-4 h-4 text-rose-600" /></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-xs font-medium text-slate-700">Payout Request</p>
                    <p className="text-[10px] text-slate-400">{new Date(p.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" })}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-number font-bold text-rose-600 text-xs">-{fmt(p.amount)}</p>
                    <Badge className={`${statusColors[p.status]} text-[10px] px-1.5 py-0 rounded-full border-0`}>{p.status}</Badge>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
