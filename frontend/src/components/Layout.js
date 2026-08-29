import { useAuth, API } from "@/App";
import { Outlet, useNavigate, useLocation, Link } from "react-router-dom";
import { LayoutDashboard, Users, Wallet, BookOpen, LogOut, Menu, X, Shield, Trophy, Bell, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "sonner";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/courses", label: "Courses", icon: BookOpen },
  { path: "/referrals", label: "Referrals", icon: Users },
  // { path: "/network", label: "Network", icon: GitBranch },       // HIDDEN — uncomment to bring back
  { path: "/wallet", label: "Wallet", icon: Wallet },
  // { path: "/leaderboard", label: "Leaderboard", icon: Trophy },  // HIDDEN — uncomment to bring back
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const sseRef = useRef(null);

  const allNav = user?.is_admin ? [...navItems, { path: "/admin/courses", label: "Admin", icon: Shield }] : navItems;

  // SSE for real-time notifications
  useEffect(() => {
    fetchUnread();
    
    // Setup SSE connection
    const setupSSE = () => {
      try {
        const eventSource = new EventSource(`${API}/notifications/stream`, { withCredentials: true });
        sseRef.current = eventSource;
        
        eventSource.addEventListener("notification", (e) => {
          const data = JSON.parse(e.data);
          setUnreadCount(data.unread_count);
          // Show toast for new notification
          toast.info(data.title, { description: data.message, duration: 5000 });
        });
        
        eventSource.addEventListener("unread_count", (e) => {
          const data = JSON.parse(e.data);
          setUnreadCount(data.count);
        });
        
        eventSource.onerror = () => {
          // Fallback to polling if SSE fails
          eventSource.close();
          sseRef.current = null;
        };
      } catch {
        // SSE not supported, fallback to polling
      }
    };
    
    setupSSE();
    
    // Fallback polling
    const interval = setInterval(fetchUnread, 30000);
    
    return () => {
      clearInterval(interval);
      if (sseRef.current) {
        sseRef.current.close();
      }
    };
  }, []);

  const fetchUnread = async () => {
    try { const res = await axios.get(`${API}/notifications/unread-count`, { withCredentials: true }); setUnreadCount(res.data.count); } catch {}
  };

  const openNotifs = async () => {
    try {
      const res = await axios.get(`${API}/notifications`, { withCredentials: true });
      setNotifications(res.data.slice(0, 10));
      if (unreadCount > 0) { await axios.post(`${API}/notifications/mark-read`, {}, { withCredentials: true }); setUnreadCount(0); }
    } catch {}
  };

  const handleLogout = async () => { await logout(); navigate("/login", { replace: true }); };

  const notifColors = { commission: "text-emerald-600 bg-emerald-50", referral: "text-indigo-600 bg-indigo-50", certificate: "text-amber-600 bg-amber-50", quiz: "text-purple-600 bg-purple-50", payout: "text-rose-600 bg-rose-50", info: "text-slate-600 bg-slate-50" };

  return (
    <div className="min-h-screen bg-[#F8FAFC] font-body">
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link to="/dashboard" className="flex items-center gap-2" data-testid="logo-link">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
              </div>
              <span className="font-heading font-bold text-slate-900 text-base hidden sm:block">Mera Mentor</span>
            </Link>

            <div className="hidden md:flex items-center gap-0.5">
              {allNav.map((item) => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
                return (
                  <Link key={item.path} to={item.path} data-testid={`nav-${item.label.toLowerCase()}`}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"}`}>
                    <item.icon className="w-3.5 h-3.5" /> {item.label}
                  </Link>
                );
              })}
            </div>

            <div className="flex items-center gap-1.5">
              {/* Notifications */}
              <Popover open={notifOpen} onOpenChange={(o) => { setNotifOpen(o); if (o) openNotifs(); }}>
                <PopoverTrigger asChild>
                  <button data-testid="notification-bell" className="relative p-2 text-slate-400 hover:text-slate-600 transition-colors" aria-label="Notifications">
                    <Bell className="w-4 h-4" />
                    {unreadCount > 0 && <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">{unreadCount > 9 ? "9+" : unreadCount}</span>}
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-80 p-0 max-h-96 overflow-y-auto" align="end">
                  <div className="p-3 border-b border-slate-100"><h3 className="font-heading font-semibold text-sm text-slate-900">Notifications</h3></div>
                  {notifications.length === 0 ? (
                    <div className="p-6 text-center"><p className="text-xs text-slate-400">No notifications yet</p></div>
                  ) : (
                    <div className="divide-y divide-slate-50">
                      {notifications.map((n) => (
                        <div key={n.notification_id} className="px-3 py-2.5 hover:bg-slate-50 transition-colors">
                          <div className="flex items-start gap-2">
                            <div className={`w-6 h-6 rounded-full ${notifColors[n.type] || notifColors.info} flex items-center justify-center shrink-0 mt-0.5`}>
                              {n.type === "commission" ? <span className="text-[10px]">₹</span> : n.type === "referral" ? <Users className="w-3 h-3" /> : n.type === "certificate" ? <Trophy className="w-3 h-3" /> : <Bell className="w-3 h-3" />}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-slate-700">{n.title}</p>
                              <p className="text-[10px] text-slate-400 mt-0.5">{n.message}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </PopoverContent>
              </Popover>

              {/* Streak */}
              {user?.streak > 0 && (
                <div className="hidden sm:flex items-center gap-1 px-2 py-1 bg-orange-50 rounded-full" data-testid="streak-badge">
                  <span className="text-orange-500 text-xs">🔥</span>
                  <span className="font-number text-[10px] font-bold text-orange-600">{user.streak}</span>
                </div>
              )}

              <div className="hidden sm:flex items-center gap-1.5 ml-1">
                <div className="w-7 h-7 rounded-full overflow-hidden border border-slate-200">
                  {user?.picture ? <img src={user.picture} alt={user.name} className="w-full h-full object-cover" /> : <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold">{user?.name?.[0]}</div>}
                </div>
              </div>
              <Button data-testid="logout-btn" variant="ghost" size="sm" onClick={handleLogout} className="text-slate-400 hover:text-red-500 hover:bg-red-50 h-8 w-8 p-0"><LogOut className="w-3.5 h-3.5" /></Button>
              <button data-testid="mobile-menu-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden p-1.5 text-slate-500" aria-label="Menu">
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white animate-slide-up">
            <div className="px-4 py-2 space-y-0.5">
              {allNav.map((item) => (
                <Link key={item.path} to={item.path} onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${location.pathname === item.path ? "bg-indigo-50 text-indigo-600" : "text-slate-600 hover:bg-slate-50"}`}>
                  <item.icon className="w-4 h-4" /> {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6"><Outlet /></main>
    </div>
  );
}
