import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { Trophy, Medal, Crown, Star, TrendingUp, Users } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const badgeConfig = {
  diamond: { label: "Diamond", color: "bg-cyan-100 text-cyan-700", icon: Crown },
  gold: { label: "Gold", color: "bg-amber-100 text-amber-700", icon: Crown },
  silver: { label: "Silver", color: "bg-slate-200 text-slate-700", icon: Medal },
  bronze: { label: "Bronze", color: "bg-orange-100 text-orange-700", icon: Medal },
  none: { label: "", color: "", icon: null },
};

export default function Leaderboard() {
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState([]);
  const [period, setPeriod] = useState("all");
  const [myRank, setMyRank] = useState(null);

  useEffect(() => { fetchLeaderboard(); }, [period]);
  useEffect(() => { fetchMyRank(); }, []);

  const fetchLeaderboard = async () => {
    try { const res = await axios.get(`${API}/leaderboard?period=${period}`, { withCredentials: true }); setLeaderboard(res.data); } catch {}
  };
  const fetchMyRank = async () => {
    try { const res = await axios.get(`${API}/leaderboard/my-rank`, { withCredentials: true }); setMyRank(res.data); } catch {}
  };

  const fmt = (v) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(v);

  const podiumColors = ["from-amber-400 to-yellow-500", "from-slate-300 to-slate-400", "from-orange-300 to-orange-400"];
  const podiumHeights = ["h-28", "h-20", "h-16"];

  return (
    <div className="animate-slide-up" data-testid="leaderboard-page">
      <div className="mb-5">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Leaderboard</h1>
        <p className="text-slate-400 font-body text-sm">Top earners on Mera Mentor</p>
      </div>

      {/* My Rank Card */}
      {myRank && (
        <Card className="bg-gradient-to-r from-indigo-600 to-indigo-800 rounded-xl p-5 mb-6 text-white relative overflow-hidden">
          <div className="absolute inset-0 header-texture" />
          <div className="relative z-10 flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center">
              {myRank.rank > 0 ? <span className="font-number text-xl font-extrabold">#{myRank.rank}</span> : <span className="text-xs">N/A</span>}
            </div>
            <div className="flex-1">
              <p className="text-white/70 text-[10px] uppercase tracking-wider">Your Rank</p>
              <p className="font-heading font-bold text-lg">{user?.name}</p>
            </div>
            <div className="text-right space-y-1">
              <div className="flex items-center gap-2 justify-end">
                <span className="text-white/60 text-[10px]">Earned</span>
                <span className="font-number font-bold text-sm">{fmt(myRank.total_earned)}</span>
              </div>
              <div className="flex items-center gap-2 justify-end">
                <span className="text-white/60 text-[10px]">Referrals</span>
                <span className="font-number font-bold text-sm">{myRank.total_referrals}</span>
              </div>
              <div className="flex items-center gap-2 justify-end">
                <span className="text-white/60 text-[10px]">XP</span>
                <span className="font-number font-bold text-sm">{myRank.xp}</span>
              </div>
            </div>
            {myRank.badge !== "none" && (
              <Badge className={`${badgeConfig[myRank.badge]?.color} border-0 text-xs px-3 py-1`}>
                {badgeConfig[myRank.badge]?.label}
              </Badge>
            )}
          </div>
        </Card>
      )}

      {/* Badge Legend */}
      <div className="flex flex-wrap gap-2 mb-5">
        {[
          { badge: "bronze", req: "5+ referrals" },
          { badge: "silver", req: "20+ referrals" },
          { badge: "gold", req: "50+ referrals" },
          { badge: "diamond", req: "100+ referrals" },
        ].map(b => (
          <div key={b.badge} className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${badgeConfig[b.badge].color} text-[10px] font-medium`}>
            {badgeConfig[b.badge].label} ({b.req})
          </div>
        ))}
      </div>

      {/* Period Toggle */}
      <Tabs value={period} onValueChange={setPeriod}>
        <TabsList className="bg-slate-100/60 p-1 rounded-full inline-flex mb-5">
          {["weekly", "monthly", "all"].map(p => (
            <TabsTrigger key={p} value={p} className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium capitalize">
              {p === "all" ? "All Time" : p}
            </TabsTrigger>
          ))}
        </TabsList>

        {["weekly", "monthly", "all"].map(p => (
          <TabsContent key={p} value={p}>
            {leaderboard.length === 0 ? (
              <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center">
                <Trophy className="w-10 h-10 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No earnings data for this period yet</p>
              </Card>
            ) : (
              <>
                {/* Top 3 Podium */}
                {leaderboard.length >= 3 && (
                  <div className="flex items-end justify-center gap-3 mb-6">
                    {[1, 0, 2].map((idx) => {
                      const entry = leaderboard[idx];
                      if (!entry) return null;
                      return (
                        <div key={entry.user_id} className="flex flex-col items-center">
                          <div className="w-12 h-12 rounded-full border-2 border-white shadow-lg overflow-hidden mb-2">
                            {entry.picture ? <img src={entry.picture} alt={entry.name} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-sm font-bold">{entry.name?.[0]}</div>}
                          </div>
                          <p className="text-xs font-semibold text-slate-800 text-center max-w-[80px] truncate">{entry.name}</p>
                          <p className="font-number text-[10px] font-bold text-indigo-600">{fmt(entry.total_earned)}</p>
                          <div className={`w-20 ${podiumHeights[idx]} bg-gradient-to-t ${podiumColors[idx]} rounded-t-xl mt-2 flex items-center justify-center`}>
                            <span className="text-white font-number font-extrabold text-lg">#{entry.rank}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Full List */}
                <div className="space-y-2">
                  {leaderboard.map((entry, idx) => (
                    <Card key={entry.user_id} className={`bg-white rounded-xl border border-slate-100 shadow-sm p-3.5 flex items-center gap-3 ${entry.user_id === user?.user_id ? "ring-2 ring-indigo-200" : ""}`} data-testid={`leaderboard-row-${idx}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-number font-bold text-xs ${idx < 3 ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-500"}`}>
                        {entry.rank}
                      </div>
                      <div className="w-8 h-8 rounded-full overflow-hidden border border-slate-200 shrink-0">
                        {entry.picture ? <img src={entry.picture} alt={entry.name} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold">{entry.name?.[0]}</div>}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-slate-800 truncate">{entry.name}</p>
                        <p className="text-[10px] text-slate-400">{entry.total_referrals} referrals &middot; {entry.xp} XP</p>
                      </div>
                      {entry.badge !== "none" && <Badge className={`${badgeConfig[entry.badge]?.color} border-0 text-[10px]`}>{badgeConfig[entry.badge]?.label}</Badge>}
                      <span className="font-number text-xs font-bold text-indigo-600">{fmt(entry.total_earned)}</span>
                    </Card>
                  ))}
                </div>
              </>
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
