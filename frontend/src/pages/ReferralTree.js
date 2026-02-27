import { useState, useEffect, useCallback } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import Tree from "react-d3-tree";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users, IndianRupee, ZoomIn, ZoomOut, RotateCcw, GitBranch, TrendingUp } from "lucide-react";

const statusColors = {
  active: "bg-emerald-100 text-emerald-700",
  pending: "bg-amber-100 text-amber-700",
  churned: "bg-red-100 text-red-700",
};

const levelColors = ["#4f46e5", "#7c3aed", "#a855f7", "#ec4899", "#f97316"];  // 5 levels

const CustomNode = ({ nodeDatum }) => {
  const level = nodeDatum.attributes?.level || 0;
  const status = nodeDatum.attributes?.status || "pending";
  const earned = nodeDatum.attributes?.earned || 0;
  const isRoot = level === 0;
  const hasChildren = nodeDatum.children && nodeDatum.children.length > 0;
  
  return (
    <g>
      {/* Node background */}
      <rect
        x={isRoot ? -80 : -60}
        y={-30}
        width={isRoot ? 160 : 120}
        height={60}
        rx={12}
        fill="white"
        stroke={levelColors[level] || "#94a3b8"}
        strokeWidth={isRoot ? 3 : 2}
        style={{ filter: "drop-shadow(0 2px 4px rgba(0,0,0,0.1))" }}
      />
      
      {/* Level indicator */}
      <circle cx={isRoot ? -65 : -45} cy={-15} r={10} fill={levelColors[level] || "#94a3b8"} />
      <text x={isRoot ? -65 : -45} y={-11} textAnchor="middle" fill="white" fontSize={9} fontWeight="bold">
        L{level}
      </text>
      
      {/* Name */}
      <text x={0} y={-8} textAnchor="middle" fill="#1e293b" fontSize={11} fontWeight="600">
        {nodeDatum.name?.length > 14 ? nodeDatum.name.substring(0, 14) + "…" : nodeDatum.name}
      </text>
      
      {/* Status badge */}
      <rect x={isRoot ? -30 : -25} y={2} width={isRoot ? 60 : 50} height={16} rx={8} fill={status === "active" ? "#d1fae5" : status === "churned" ? "#fee2e2" : "#fef3c7"} />
      <text x={0} y={13} textAnchor="middle" fontSize={8} fill={status === "active" ? "#065f46" : status === "churned" ? "#991b1b" : "#92400e"}>
        {status.toUpperCase()}
      </text>
      
      {/* Earned amount */}
      {earned > 0 && (
        <text x={0} y={28} textAnchor="middle" fontSize={9} fill="#6366f1" fontWeight="500">
          ₹{earned.toLocaleString("en-IN")}
        </text>
      )}
      
      {/* Children count indicator */}
      {hasChildren && (
        <>
          <circle cx={isRoot ? 55 : 40} cy={0} r={10} fill="#e0e7ff" />
          <text x={isRoot ? 55 : 40} y={4} textAnchor="middle" fontSize={9} fill="#4f46e5" fontWeight="bold">
            {nodeDatum.children.length}
          </text>
        </>
      )}
    </g>
  );
};

export default function ReferralTree() {
  const { user } = useAuth();
  const [treeData, setTreeData] = useState(null);
  const [treeStats, setTreeStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState(0.7);
  const [translate, setTranslate] = useState({ x: 400, y: 50 });
  
  useEffect(() => {
    fetchTreeData();
  }, []);
  
  const fetchTreeData = async () => {
    setLoading(true);
    try {
      const [treeRes, statsRes] = await Promise.all([
        axios.get(`${API}/referrals/tree`, { withCredentials: true }),
        axios.get(`${API}/referrals/tree-stats`, { withCredentials: true }),
      ]);
      setTreeData(treeRes.data);
      setTreeStats(statsRes.data);
    } catch (e) {
      console.error("Failed to load tree", e);
    }
    setLoading(false);
  };
  
  const fmt = (v) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(v);
  
  const handleZoomIn = () => setZoom(z => Math.min(z + 0.15, 2));
  const handleZoomOut = () => setZoom(z => Math.max(z - 0.15, 0.3));
  const handleReset = () => { setZoom(0.7); setTranslate({ x: 400, y: 50 }); };
  
  if (loading) return <div className="flex items-center justify-center py-20"><div className="loader"></div></div>;
  
  return (
    <div className="animate-slide-up" data-testid="referral-tree-page">
      <div className="mb-5">
        <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Referral Network</h1>
        <p className="text-slate-400 font-body text-sm">Visualize your 7-level referral tree</p>
      </div>
      
      {/* Stats Cards */}
      {treeStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center"><Users className="w-4 h-4 text-indigo-600" /></div>
              <div><p className="text-[10px] text-slate-400 uppercase">Total Network</p><p className="font-number text-lg font-extrabold text-slate-900">{treeStats.total_network}</p></div>
            </div>
          </Card>
          
          {treeStats.by_level?.slice(0, 3).map((l, i) => (
            <Card key={l.level} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${levelColors[i]}15` }}>
                  <span className="font-number text-sm font-bold" style={{ color: levelColors[i] }}>L{l.level}</span>
                </div>
                <div>
                  <p className="text-[10px] text-slate-400 uppercase">Level {l.level}</p>
                  <p className="font-number text-lg font-extrabold text-slate-900">{l.count}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
      
      {/* Level Earnings Summary */}
      {treeStats?.earnings_by_level && Object.keys(treeStats.earnings_by_level).length > 0 && (
        <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 mb-5">
          <h3 className="font-heading font-semibold text-sm text-slate-900 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-500" /> Earnings by Level
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(treeStats.earnings_by_level).map(([level, data]) => (
              <div key={level} className="px-3 py-2 rounded-lg" style={{ backgroundColor: `${levelColors[parseInt(level)-1] || '#94a3b8'}15` }}>
                <span className="text-[10px] text-slate-500">L{level}</span>
                <p className="font-number text-sm font-bold" style={{ color: levelColors[parseInt(level)-1] || '#64748b' }}>
                  {fmt(data.amount)}
                </p>
                <p className="text-[9px] text-slate-400">{data.transactions} txns</p>
              </div>
            ))}
          </div>
        </Card>
      )}
      
      {/* Tree Visualization */}
      <Card className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-3 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-4 h-4 text-indigo-500" />
            <span className="font-heading font-semibold text-sm text-slate-800">Network Tree</span>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="outline" size="sm" onClick={handleZoomOut} className="h-7 w-7 p-0 rounded-lg" data-testid="zoom-out-btn">
              <ZoomOut className="w-3.5 h-3.5" />
            </Button>
            <span className="text-[10px] text-slate-500 w-10 text-center font-number">{Math.round(zoom * 100)}%</span>
            <Button variant="outline" size="sm" onClick={handleZoomIn} className="h-7 w-7 p-0 rounded-lg" data-testid="zoom-in-btn">
              <ZoomIn className="w-3.5 h-3.5" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleReset} className="h-7 px-2 rounded-lg ml-1" data-testid="reset-zoom-btn">
              <RotateCcw className="w-3 h-3 mr-1" /> Reset
            </Button>
          </div>
        </div>
        
        <div className="h-[500px] bg-slate-50/50" data-testid="tree-container">
          {treeData ? (
            <Tree
              data={treeData}
              orientation="vertical"
              pathFunc="step"
              translate={translate}
              zoom={zoom}
              onUpdate={({ translate: t, zoom: z }) => { setTranslate(t); setZoom(z); }}
              separation={{ siblings: 1.5, nonSiblings: 2 }}
              nodeSize={{ x: 180, y: 120 }}
              renderCustomNodeElement={(rd3tProps) => <CustomNode {...rd3tProps} />}
              pathClassFunc={() => "stroke-slate-300 stroke-[1.5]"}
              collapsible={true}
              enableLegacyTransitions={true}
              transitionDuration={300}
            />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No referrals yet</p>
                <p className="text-slate-400 text-xs mt-1">Share your referral link to build your network</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Legend */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex flex-wrap items-center gap-3 text-[10px]">
            <span className="text-slate-500 font-medium">Legend:</span>
            {[0, 1, 2, 3, 4, 5].map(l => (
              <div key={l} className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: levelColors[l] || "#94a3b8" }} />
                <span className="text-slate-600">{l === 0 ? "You" : `L${l}`}</span>
              </div>
            ))}
            <span className="text-slate-300 mx-2">|</span>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-emerald-400" /><span className="text-slate-600">Active</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-amber-400" /><span className="text-slate-600">Pending</span></div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-red-400" /><span className="text-slate-600">Churned</span></div>
          </div>
        </div>
      </Card>
    </div>
  );
}
