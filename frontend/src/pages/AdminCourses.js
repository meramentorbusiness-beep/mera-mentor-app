import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Plus, Trash2, GripVertical, Save, Eye, EyeOff, Video, FileText, Users, IndianRupee, ShoppingBag } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function AdminCourses() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [saving, setSaving] = useState(false);

  const emptyCourse = {
    title: "", description: "", price: 500, original_price: 999,
    image: "", category: "Development", tier: "standard",
    is_upsell: false, upsell_for: "", published: true,
    lessons: [], resources: [],
  };

  useEffect(() => {
    if (!user?.is_admin) return;
    fetchCourses();
    fetchStats();
  }, [user]);

  const fetchCourses = async () => {
    try {
      const res = await axios.get(`${API}/courses`);
      setCourses(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/admin/stats`, { withCredentials: true });
      setAdminStats(res.data);
    } catch (e) { console.error(e); }
  };

  const openNew = () => { setEditingCourse({ ...emptyCourse }); setEditOpen(true); };
  const openEdit = (course) => { setEditingCourse({ ...course }); setEditOpen(true); };

  const addLesson = () => {
    setEditingCourse((prev) => ({
      ...prev,
      lessons: [...(prev.lessons || []), { title: "", description: "", video_url: "", duration: "" }],
    }));
  };

  const updateLesson = (idx, field, value) => {
    setEditingCourse((prev) => {
      const lessons = [...prev.lessons];
      lessons[idx] = { ...lessons[idx], [field]: value };
      return { ...prev, lessons };
    });
  };

  const removeLesson = (idx) => {
    setEditingCourse((prev) => ({
      ...prev,
      lessons: prev.lessons.filter((_, i) => i !== idx),
    }));
  };

  const addResource = () => {
    setEditingCourse((prev) => ({
      ...prev,
      resources: [...(prev.resources || []), { name: "", type: "pdf", url: "" }],
    }));
  };

  const updateResource = (idx, field, value) => {
    setEditingCourse((prev) => {
      const resources = [...prev.resources];
      resources[idx] = { ...resources[idx], [field]: value };
      return { ...prev, resources };
    });
  };

  const removeResource = (idx) => {
    setEditingCourse((prev) => ({
      ...prev,
      resources: prev.resources.filter((_, i) => i !== idx),
    }));
  };

  const saveCourse = async () => {
    if (!editingCourse.title) { toast.error("Title is required"); return; }
    setSaving(true);
    try {
      if (editingCourse.course_id) {
        await axios.put(`${API}/admin/courses/${editingCourse.course_id}`, editingCourse, { withCredentials: true });
        toast.success("Course updated!");
      } else {
        await axios.post(`${API}/admin/courses`, editingCourse, { withCredentials: true });
        toast.success("Course created!");
      }
      setEditOpen(false);
      fetchCourses();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const deleteCourse = async (courseId) => {
    if (!window.confirm("Delete this course?")) return;
    try {
      await axios.delete(`${API}/admin/courses/${courseId}`, { withCredentials: true });
      toast.success("Course deleted");
      fetchCourses();
    } catch (e) {
      toast.error("Delete failed");
    }
  };

  const fmt = (val) => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 0 }).format(val);

  if (!user?.is_admin) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-500 font-body">Admin access required</p>
      </div>
    );
  }

  return (
    <div className="animate-slide-up" data-testid="admin-courses-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold text-slate-900 mb-0.5">Admin Panel</h1>
          <p className="text-slate-400 font-body text-sm">Manage courses, lessons and platform</p>
        </div>
        <Button data-testid="create-course-btn" onClick={openNew} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-5 text-xs font-semibold">
          <Plus className="w-4 h-4 mr-1" /> New Course
        </Button>
      </div>

      {/* Admin Stats */}
      {adminStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          {[
            { label: "Total Users", value: adminStats.total_users, icon: Users, color: "bg-indigo-50 text-indigo-600" },
            { label: "Purchases", value: adminStats.total_purchases, icon: ShoppingBag, color: "bg-emerald-50 text-emerald-600" },
            { label: "Revenue", value: fmt(adminStats.total_revenue), icon: IndianRupee, color: "bg-amber-50 text-amber-600" },
            { label: "Commissions", value: fmt(adminStats.total_commissions), icon: IndianRupee, color: "bg-rose-50 text-rose-600" },
          ].map((s, i) => (
            <Card key={i} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4">
              <div className="flex items-center gap-2.5">
                <div className={`w-9 h-9 rounded-lg ${s.color} flex items-center justify-center`}><s.icon className="w-4 h-4" /></div>
                <div>
                  <p className="text-[10px] text-slate-400 font-body uppercase tracking-wider">{s.label}</p>
                  <p className="font-number text-lg font-bold text-slate-900">{s.value}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Course List */}
      <div className="space-y-3">
        {courses.map((course, idx) => (
          <Card key={course.course_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-4" data-testid={`admin-course-row-${idx}`}>
            <img src={course.image} alt={course.title} className="w-16 h-12 rounded-lg object-cover shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-heading font-semibold text-slate-900 text-sm truncate">{course.title}</h3>
                {course.is_upsell && <Badge className="bg-purple-100 text-purple-700 border-0 text-[10px]">Upsell</Badge>}
                {!course.published && <Badge className="bg-slate-100 text-slate-500 border-0 text-[10px]">Draft</Badge>}
              </div>
              <p className="text-xs text-slate-400 font-body">{course.category} &middot; {course.lesson_count || course.lessons?.length || 0} lessons &middot; {fmt(course.price)}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Button variant="outline" size="sm" onClick={() => openEdit(course)} className="text-xs rounded-lg h-8" data-testid={`edit-course-btn-${idx}`}>Edit</Button>
              <Button variant="ghost" size="sm" onClick={() => deleteCourse(course.course_id)} className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0" data-testid={`delete-course-btn-${idx}`}>
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {/* Edit/Create Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">{editingCourse?.course_id ? "Edit Course" : "Create Course"}</DialogTitle>
          </DialogHeader>

          {editingCourse && (
            <div className="space-y-4 py-2">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs font-body">Title</Label>
                  <Input data-testid="course-title-input" value={editingCourse.title} onChange={(e) => setEditingCourse({ ...editingCourse, title: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label className="text-xs font-body">Category</Label>
                  <Select value={editingCourse.category} onValueChange={(v) => setEditingCourse({ ...editingCourse, category: v })}>
                    <SelectTrigger className="mt-1" data-testid="course-category-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {["Development", "Data Science", "Marketing", "Design", "Business", "Bundle", "General"].map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label className="text-xs font-body">Description</Label>
                <Textarea data-testid="course-description-input" value={editingCourse.description} onChange={(e) => setEditingCourse({ ...editingCourse, description: e.target.value })} className="mt-1" rows={3} />
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label className="text-xs font-body">Price (INR)</Label>
                  <Input data-testid="course-price-input" type="number" min="0" value={editingCourse.price} onChange={(e) => setEditingCourse({ ...editingCourse, price: parseFloat(e.target.value) || 0 })} className="mt-1 font-number" />
                </div>
                <div>
                  <Label className="text-xs font-body">Original Price</Label>
                  <Input type="number" min="0" value={editingCourse.original_price} onChange={(e) => setEditingCourse({ ...editingCourse, original_price: parseFloat(e.target.value) || 0 })} className="mt-1 font-number" />
                </div>
                <div>
                  <Label className="text-xs font-body">Image URL</Label>
                  <Input value={editingCourse.image} onChange={(e) => setEditingCourse({ ...editingCourse, image: e.target.value })} className="mt-1" placeholder="https://..." />
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch checked={editingCourse.published} onCheckedChange={(v) => setEditingCourse({ ...editingCourse, published: v })} />
                  <Label className="text-xs font-body">Published</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={editingCourse.is_upsell} onCheckedChange={(v) => setEditingCourse({ ...editingCourse, is_upsell: v })} />
                  <Label className="text-xs font-body">Is Upsell</Label>
                </div>
              </div>

              {/* Lessons */}
              <div className="border-t border-slate-100 pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-heading font-semibold text-sm text-slate-900 flex items-center gap-1.5"><Video className="w-4 h-4 text-indigo-500" /> Lessons</h3>
                  <Button variant="outline" size="sm" onClick={addLesson} className="text-xs rounded-lg h-7" data-testid="add-lesson-btn">
                    <Plus className="w-3 h-3 mr-1" /> Add Lesson
                  </Button>
                </div>
                <div className="space-y-3">
                  {editingCourse.lessons?.map((lesson, idx) => (
                    <Card key={idx} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                      <div className="flex items-start gap-2">
                        <span className="text-xs font-bold text-slate-400 font-number mt-2 w-5">{idx + 1}</span>
                        <div className="flex-1 space-y-2">
                          <Input data-testid={`lesson-title-${idx}`} placeholder="Lesson title" value={lesson.title} onChange={(e) => updateLesson(idx, "title", e.target.value)} className="text-xs h-8" />
                          <Input placeholder="YouTube embed URL (youtube-nocookie.com)" value={lesson.video_url} onChange={(e) => updateLesson(idx, "video_url", e.target.value)} className="text-xs h-8" />
                          <div className="grid grid-cols-2 gap-2">
                            <Input placeholder="Description" value={lesson.description} onChange={(e) => updateLesson(idx, "description", e.target.value)} className="text-xs h-8" />
                            <Input placeholder="Duration (e.g. 15 min)" value={lesson.duration} onChange={(e) => updateLesson(idx, "duration", e.target.value)} className="text-xs h-8" />
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeLesson(idx)} className="text-red-400 hover:text-red-600 h-8 w-8 p-0 mt-0.5">
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Resources */}
              <div className="border-t border-slate-100 pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-heading font-semibold text-sm text-slate-900 flex items-center gap-1.5"><FileText className="w-4 h-4 text-indigo-500" /> Resources</h3>
                  <Button variant="outline" size="sm" onClick={addResource} className="text-xs rounded-lg h-7" data-testid="add-resource-btn">
                    <Plus className="w-3 h-3 mr-1" /> Add Resource
                  </Button>
                </div>
                <div className="space-y-2">
                  {editingCourse.resources?.map((res, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <Input placeholder="Resource name" value={res.name} onChange={(e) => updateResource(idx, "name", e.target.value)} className="text-xs h-8 flex-1" />
                      <Select value={res.type} onValueChange={(v) => updateResource(idx, "type", v)}>
                        <SelectTrigger className="w-24 h-8 text-xs"><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="pdf">PDF</SelectItem>
                          <SelectItem value="doc">DOC</SelectItem>
                          <SelectItem value="link">Link</SelectItem>
                        </SelectContent>
                      </Select>
                      <Input placeholder="URL" value={res.url} onChange={(e) => updateResource(idx, "url", e.target.value)} className="text-xs h-8 flex-1" />
                      <Button variant="ghost" size="sm" onClick={() => removeResource(idx)} className="text-red-400 h-8 w-8 p-0"><Trash2 className="w-3.5 h-3.5" /></Button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)} className="rounded-full text-xs">Cancel</Button>
            <Button data-testid="save-course-btn" onClick={saveCourse} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs">
              {saving ? "Saving..." : <><Save className="w-3.5 h-3.5 mr-1" /> Save Course</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
