import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, Navigate } from "react-router-dom";
import axios from "axios";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);
export { API, BACKEND_URL };

import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import ReferredUsers from "@/pages/ReferredUsers";
import Wallet from "@/pages/Wallet";
import Courses from "@/pages/Courses";
import CourseDetail from "@/pages/CourseDetail";
import Upsell from "@/pages/Upsell";
import AdminCourses from "@/pages/AdminCourses";
import Leaderboard from "@/pages/Leaderboard";
import ReferralLanding from "@/pages/ReferralLanding";
import ReferralTree from "@/pages/ReferralTree";
import Layout from "@/components/Layout";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  useEffect(() => { if (!loading && !user) navigate("/login", { replace: true }); }, [user, loading, navigate]);
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="loader"></div></div>;
  return user ? children : null;
}

function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/ref/:code" element={<ReferralLanding />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="referrals" element={<ReferredUsers />} />
        <Route path="wallet" element={<Wallet />} />
        <Route path="courses" element={<Courses />} />
        <Route path="courses/:courseId" element={<CourseDetail />} />
        <Route path="upsell/:courseId" element={<Upsell />} />
        <Route path="leaderboard" element={<Leaderboard />} />
        <Route path="network" element={<ReferralTree />} />
        <Route path="admin/courses" element={<AdminCourses />} />
      </Route>
    </Routes>
  );
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const checkAuth = async () => {
    try { const res = await axios.get(`${API}/auth/me`, { withCredentials: true }); setUser(res.data); } catch { setUser(null); } finally { setLoading(false); }
  };
  const updateUser = (data) => setUser(data);
  const logout = async () => { try { await axios.post(`${API}/auth/logout`, {}, { withCredentials: true }); } finally { setUser(null); } };
  useEffect(() => { checkAuth(); }, []);
  return <AuthContext.Provider value={{ user, loading, checkAuth, updateUser, logout }}>{children}</AuthContext.Provider>;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}
export default App;
