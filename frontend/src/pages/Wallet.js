import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { IndianRupee, ArrowUpRight, ArrowDownLeft, Clock, CheckCircle, Wallet as WalletIcon, Download, FileText, AlertCircle, Calendar } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export default function Wallet() {
  const { user } = useAuth();
  const [wallet, setWallet] = useState({ balance: 0, total_earned: 0, total_withdrawn: 0 });
  const [transactions, setTransactions] = useState({ commissions: [], payouts: [] });
  const [payoutAmount, setPayoutAmount] = useState("");
  const [payoutPreview, setPayoutPreview] = useState(null);
  const [payoutOpen, setPayoutOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => { fetchWallet(); fetchTransactions(); }, []);

  const fetchWallet = async () => {
    try { const res = await axios.get(`${API}/wallet`, { withCredentials: true }); setWallet(res.data); } catch (e) { console.error(e); }
  };
  const fetchTransactions = async () => {
    try { const res = await axios.get(`${API}/wallet/transactions`, { withCredentials: true }); setTransactions(res.data); } catch (e) { console.error(e); }
  };

  const previewPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) { toast.error("Enter a valid amount"); return; }
    setPreviewLoading(true);
    try {
      const res = await axios.post(`${API}/wallet/payout/preview`, { amount }, { withCredentials: true });
      setPayoutPreview(res.data);
    } catch (e) { toast.error(e.response?.data?.detail || "Preview failed"); }
    finally { setPreviewLoading(false); }
  };

  const requestPayout = async () => {
    const amount = parseFloat(payoutAmount);
    if (!amount || amount <= 0) { toast.error("Enter a valid amount"); return; }
    setSubmitting(true);
    try {
      const res = await axios.post(`${API}/wallet/payout`, { amount }, { withCredentials: true });
      toast.success(`Payout of ${fmt(res.data.net)} requested! Expected by ${res.data.estimated_date}`);
      setPayoutOpen(false); setPayoutAmount(""); setPayoutPreview(null); fetchWallet(); fetchTransactions();
    } catch (e) { toast.error(e.response?.data?.detail || "Payout failed"); }
    finally { setSubmitting(false); }
  };

  const downloadReceipt = async (payoutId) => {
    try {
      const res = await axios.get(`${API}/wallet/payouts/${payoutId}/receipt`, { withCredentials: true });
      const receipt = res.data;
      // Generate simple PDF-like content (HTML for printing)
      const html = `
        <!DOCTYPE html>
        <html><head><title>Payout Receipt - ${receipt.receipt_id}</title>
        <style>
          body { font-family: 'Inter', Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
          .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #4f46e5; padding-bottom: 20px; }
          .logo { font-size: 24px; font-weight: bold; color: #4f46e5; }
          .receipt-id { font-size: 12px; color: #64748b; margin-top: 5px; }
          .section { margin: 20px 0; }
          .row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
          .label { color: #64748b; font-size: 13px; }
          .value { font-weight: 600; font-size: 14px; }
          .total { background: #f1f5f9; padding: 15px; border-radius: 8px; margin-top: 20px; }
          .total .row { border: none; }
          .tds-note { font-size: 11px; color: #94a3b8; margin-top: 20px; padding: 10px; background: #fef3c7; border-radius: 6px; }
          .footer { text-align: center; margin-top: 30px; font-size: 11px; color: #94a3b8; }
        </style></head><body>
          <div class="header">
            <div class="logo">Mera Mentor</div>
            <div>Payout Receipt</div>
            <div class="receipt-id">${receipt.receipt_id}</div>
          </div>
          <div class="section">
            <div class="row"><span class="label">Recipient</span><span class="value">${receipt.user_name}</span></div>
            <div class="row"><span class="label">Email</span><span class="value">${receipt.user_email}</span></div>
            <div class="row"><span class="label">Request Date</span><span class="value">${receipt.requested_date}</span></div>
            <div class="row"><span class="label">Status</span><span class="value" style="color: ${receipt.status === 'paid' ? '#10b981' : '#f59e0b'};">${receipt.status.toUpperCase()}</span></div>
            ${receipt.estimated_date ? `<div class="row"><span class="label">Expected By</span><span class="value">${receipt.estimated_date}</span></div>` : ''}
          </div>
          <div class="total">
            <div class="row"><span class="label">Gross Amount</span><span class="value">₹${receipt.gross_amount.toLocaleString('en-IN')}</span></div>
            ${receipt.tds_amount > 0 ? `<div class="row"><span class="label">TDS Deducted (${receipt.tds_rate}%)</span><span class="value" style="color: #ef4444;">-₹${receipt.tds_amount.toLocaleString('en-IN')}</span></div>` : ''}
            <div class="row"><span class="label" style="font-weight: 600;">Net Payout</span><span class="value" style="color: #4f46e5; font-size: 18px;">₹${receipt.net_amount.toLocaleString('en-IN')}</span></div>
          </div>
          ${receipt.tds_amount > 0 ? `<div class="tds-note">${receipt.pan_note}</div>` : ''}
          <div class="footer">This is a computer-generated receipt. No signature required.<br/>Platform: ${receipt.platform}</div>
        </body></html>
      `;
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, '_blank');
      win.print();
      toast.success("Receipt opened for printing");
    } catch (e) { toast.error("Failed to generate receipt"); }
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
        <Dialog open={payoutOpen} onOpenChange={(open) => { setPayoutOpen(open); if (!open) { setPayoutPreview(null); setPayoutAmount(""); } }}>
          <DialogTrigger asChild>
            <Button data-testid="request-payout-btn" className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-full shadow-lg shadow-indigo-500/15 text-xs">
              <IndianRupee className="w-3.5 h-3.5 mr-1" /> Request Payout
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="font-heading text-lg">Request Payout</DialogTitle>
              <DialogDescription className="font-body text-xs">Available: {fmt(wallet.balance)}. Min: {fmt(100)}</DialogDescription>
            </DialogHeader>
            
            <div className="py-3 space-y-4">
              <div className="flex gap-2">
                <Input data-testid="payout-amount-input" type="number" min="100" max={wallet.balance} value={payoutAmount} onChange={(e) => { setPayoutAmount(e.target.value); setPayoutPreview(null); }} placeholder="Enter amount" className="font-number text-base h-11" />
                <Button variant="outline" onClick={previewPayout} disabled={previewLoading} className="shrink-0 text-xs" data-testid="preview-payout-btn">
                  {previewLoading ? "..." : "Preview"}
                </Button>
              </div>
              
              {payoutPreview && (
                <Card className="bg-slate-50 border border-slate-200 p-4 space-y-2 animate-slide-up">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-500">Gross Amount</span>
                    <span className="font-number font-semibold text-slate-700">{fmt(payoutPreview.gross)}</span>
                  </div>
                  {payoutPreview.tds > 0 && (
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3 text-amber-500" /> TDS ({payoutPreview.tds_rate}%)
                      </span>
                      <span className="font-number font-semibold text-red-600">-{fmt(payoutPreview.tds)}</span>
                    </div>
                  )}
                  <div className="border-t border-slate-200 pt-2 flex justify-between text-sm">
                    <span className="font-medium text-slate-700">Net Payout</span>
                    <span className="font-number font-bold text-indigo-600">{fmt(payoutPreview.net)}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-500 pt-1">
                    <Calendar className="w-3 h-3" />
                    <span>Expected by <strong>{payoutPreview.estimated_date}</strong> ({payoutPreview.processing_days})</span>
                  </div>
                  {payoutPreview.tds > 0 && (
                    <p className="text-[10px] text-amber-700 bg-amber-50 px-2 py-1.5 rounded">
                      TDS is deducted for payouts above ₹5,000 as per Income Tax regulations.
                    </p>
                  )}
                </Card>
              )}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setPayoutOpen(false)} className="rounded-full text-xs">Cancel</Button>
              <Button data-testid="confirm-payout-btn" onClick={requestPayout} disabled={submitting || !payoutPreview} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs">
                {submitting ? "Processing..." : `Confirm Payout (${payoutPreview ? fmt(payoutPreview.net) : ""})`}
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
                    <div className="flex items-center gap-2 text-[10px] text-slate-400">
                      <span>{new Date(p.created_at).toLocaleDateString("en-IN")}</span>
                      {p.tds_amount > 0 && <span className="text-amber-600">TDS: {fmt(p.tds_amount)}</span>}
                      {p.estimated_date && p.status === "pending" && (
                        <span className="text-indigo-500">Expected: {p.estimated_date.slice(0, 10)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right shrink-0">
                      <p className="font-number font-bold text-rose-600 text-xs">-{fmt(p.net_amount || p.amount)}</p>
                      <Badge className={`${statusColors[p.status]} text-[10px] px-1.5 py-0 rounded-full border-0`}>{p.status}</Badge>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => downloadReceipt(p.payout_id)} className="h-7 w-7 p-0 rounded-lg" data-testid={`download-receipt-${idx}`}>
                      <Download className="w-3.5 h-3.5 text-slate-400 hover:text-indigo-600" />
                    </Button>
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
