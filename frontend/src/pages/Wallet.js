import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { IndianRupee, ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, AlertCircle, Wallet as WalletIcon } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export default function Wallet() {
  const { user } = useAuth();
  const [wallet, setWallet] = useState({ balance: 0, total_earned: 0, total_withdrawn: 0 });
  const [transactions, setTransactions] = useState({ commissions: [], payouts: [] });
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutOpen, setPayoutOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchWallet();
    fetchTransactions();
  }, []);

  const fetchWallet = async () => {
    try {
      const res = await axios.get(`${API}/wallet`, { withCredentials: true });
      setWallet(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchTransactions = async () => {
    try {
      const res = await axios.get(`${API}/wallet/transactions`, { withCredentials: true });
      setTransactions(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const requestPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) {
      toast.error("Enter a valid amount");
      return;
    }
    setSubmitting(true);
    try {
      await axios.post(`${API}/wallet/payout`, { amount }, { withCredentials: true });
      toast.success(`Payout of ${formatCurrency(amount)} requested!`);
      setPayoutOpen(false);
      setPayoutAmount("");
      fetchWallet();
      fetchTransactions();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Payout failed");
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (val) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(val);

  const statusIcons = {
    pending: <Clock className="w-4 h-4 text-amber-500" />,
    approved: <CheckCircle className="w-4 h-4 text-emerald-500" />,
    paid: <CheckCircle className="w-4 h-4 text-indigo-500" />,
  };

  const statusColors = {
    pending: "bg-amber-100 text-amber-700",
    approved: "bg-emerald-100 text-emerald-700",
    paid: "bg-indigo-100 text-indigo-700",
  };

  return (
    <div className="animate-slide-up" data-testid="wallet-page">
      <div className="mb-6">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-1">Commission Wallet</h1>
        <p className="text-slate-500 font-body">Track your earnings and request payouts</p>
      </div>

      {/* Wallet Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 animate-slide-up animate-slide-up-1">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
              <WalletIcon className="w-5 h-5 text-emerald-600" />
            </div>
            <p className="text-sm font-medium text-slate-500 font-body">Available Balance</p>
          </div>
          <p className="font-number text-3xl font-extrabold text-slate-900" data-testid="wallet-balance">
            {formatCurrency(wallet.balance)}
          </p>
        </Card>

        <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 animate-slide-up animate-slide-up-2">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
              <ArrowDownLeft className="w-5 h-5 text-indigo-600" />
            </div>
            <p className="text-sm font-medium text-slate-500 font-body">Total Earned</p>
          </div>
          <p className="font-number text-3xl font-extrabold text-slate-900" data-testid="total-earned">
            {formatCurrency(wallet.total_earned)}
          </p>
        </Card>

        <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-6 animate-slide-up animate-slide-up-3">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center">
              <ArrowUpRight className="w-5 h-5 text-rose-600" />
            </div>
            <p className="text-sm font-medium text-slate-500 font-body">Total Withdrawn</p>
          </div>
          <p className="font-number text-3xl font-extrabold text-slate-900" data-testid="total-withdrawn">
            {formatCurrency(wallet.total_withdrawn)}
          </p>
        </Card>
      </div>

      {/* Payout Button */}
      <div className="mb-8">
        <Dialog open={payoutOpen} onOpenChange={setPayoutOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="request-payout-btn"
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-5 px-8 rounded-full shadow-lg shadow-indigo-500/20 transition-all active:scale-95"
            >
              <IndianRupee className="w-4 h-4 mr-1.5" /> Request Payout
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="font-heading">Request Payout</DialogTitle>
              <DialogDescription className="font-body">
                Available balance: {formatCurrency(wallet.balance)}. Minimum withdrawal: {formatCurrency(100)}.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <label className="text-sm font-medium text-slate-700 font-body mb-2 block">Amount (INR)</label>
              <Input
                data-testid="payout-amount-input"
                type="number"
                min="100"
                max={wallet.balance}
                value={payoutAmount}
                onChange={(e) => setPayoutAmount(e.target.value)}
                placeholder="Enter amount"
                className="font-number text-lg h-12"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPayoutOpen(false)} className="rounded-full font-body">Cancel</Button>
              <Button
                data-testid="confirm-payout-btn"
                onClick={requestPayout}
                disabled={submitting}
                className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full font-body"
              >
                {submitting ? "Processing..." : "Confirm Payout"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Transaction History */}
      <Tabs defaultValue="commissions" className="w-full">
        <TabsList className="bg-slate-100/50 p-1 rounded-full inline-flex mb-6" data-testid="transaction-tabs">
          <TabsTrigger value="commissions" className="rounded-full px-5 py-2 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm transition-all font-body text-sm">
            Commissions ({transactions.commissions.length})
          </TabsTrigger>
          <TabsTrigger value="payouts" className="rounded-full px-5 py-2 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm transition-all font-body text-sm">
            Payouts ({transactions.payouts.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="commissions">
          {transactions.commissions.length === 0 ? (
            <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-12 text-center">
              <p className="text-slate-500 font-body">No commissions yet. Share your referral link to start earning!</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {transactions.commissions.map((c, idx) => (
                <Card
                  key={c.commission_id}
                  className="bg-white rounded-xl border border-slate-100 shadow-[0_4px_15px_rgb(0,0,0,0.03)] p-4 flex items-center gap-4"
                  data-testid={`commission-row-${idx}`}
                >
                  <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center shrink-0">
                    <ArrowDownLeft className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm font-medium text-slate-800 truncate">
                      Commission from {c.from_user_name || "User"}
                    </p>
                    <p className="text-xs text-slate-500 font-body">
                      {c.course_title} &middot; Level {c.level} &middot; {new Date(c.created_at).toLocaleDateString("en-IN")}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-number font-bold text-emerald-600 text-sm">+{formatCurrency(c.amount)}</p>
                    <Badge className={`${statusColors[c.status]} text-xs px-2 py-0.5 rounded-full border-0 mt-1`}>
                      {c.status}
                    </Badge>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="payouts">
          {transactions.payouts.length === 0 ? (
            <Card className="bg-white rounded-xl border border-slate-100 shadow-[0_8px_30px_rgb(0,0,0,0.04)] p-12 text-center">
              <p className="text-slate-500 font-body">No payout requests yet.</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {transactions.payouts.map((p, idx) => (
                <Card
                  key={p.payout_id}
                  className="bg-white rounded-xl border border-slate-100 shadow-[0_4px_15px_rgb(0,0,0,0.03)] p-4 flex items-center gap-4"
                  data-testid={`payout-row-${idx}`}
                >
                  <div className="w-10 h-10 rounded-full bg-rose-50 flex items-center justify-center shrink-0">
                    <ArrowUpRight className="w-5 h-5 text-rose-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-body text-sm font-medium text-slate-800">Payout Request</p>
                    <p className="text-xs text-slate-500 font-body">
                      {new Date(p.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long", day: "numeric" })}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-number font-bold text-rose-600 text-sm">-{formatCurrency(p.amount)}</p>
                    <Badge className={`${statusColors[p.status]} text-xs px-2 py-0.5 rounded-full border-0 mt-1`}>
                      {p.status}
                    </Badge>
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
