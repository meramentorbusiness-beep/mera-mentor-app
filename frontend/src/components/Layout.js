import { useAuth } from "@/App";
import { Outlet, useNavigate, useLocation, Link } from "react-router-dom";
import { LayoutDashboard, Users, Wallet, BookOpen, LogOut, Menu, X, Settings, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/referrals", label: "Referrals", icon: Users },
  { path: "/wallet", label: "Wallet", icon: Wallet },
  { path: "/courses", label: "Courses", icon: BookOpen },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const allNav = user?.is_admin
    ? [...navItems, { path: "/admin/courses", label: "Admin", icon: Shield }]
    : navItems;

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] font-body">
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <Link to="/dashboard" className="flex items-center gap-2" data-testid="logo-link">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <span className="font-heading font-bold text-slate-900 text-base hidden sm:block">Mera Mentor</span>
            </Link>

            <div className="hidden md:flex items-center gap-0.5">
              {allNav.map((item) => {
                const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + "/");
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    data-testid={`nav-${item.label.toLowerCase()}`}
                    className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-500 hover:text-slate-800 hover:bg-slate-50"
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                );
              })}
            </div>

            <div className="flex items-center gap-2">
              <div className="hidden sm:flex items-center gap-2">
                <div className="w-7 h-7 rounded-full overflow-hidden border border-slate-200">
                  {user?.picture ? (
                    <img src={user.picture} alt={user.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold">
                      {user?.name?.[0] || "U"}
                    </div>
                  )}
                </div>
                <span className="text-xs font-medium text-slate-600 hidden lg:block max-w-[120px] truncate">{user?.name}</span>
              </div>
              <Button data-testid="logout-btn" variant="ghost" size="sm" onClick={handleLogout} className="text-slate-400 hover:text-red-500 hover:bg-red-50 h-8 w-8 p-0">
                <LogOut className="w-4 h-4" />
              </Button>
              <button data-testid="mobile-menu-toggle" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden p-1.5 text-slate-500" aria-label="Toggle menu">
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-100 bg-white animate-slide-up">
            <div className="px-4 py-2 space-y-0.5">
              {allNav.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link key={item.path} to={item.path} onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${isActive ? "bg-indigo-50 text-indigo-600" : "text-slate-600 hover:bg-slate-50"}`}>
                    <item.icon className="w-4 h-4" /> {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
