import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth, API } from "@/App";
import axios from "axios";
import { toast } from "sonner";
import { Plus, Trash2, Save, Eye, EyeOff, Video, FileText, Users, IndianRupee, ShoppingBag, Upload, X, Check, Loader2, Youtube, File, Image, Settings, BarChart3, ClipboardList, Clock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { LandingManager } from "@/components/admin/LandingManager";

// File Upload Component with drag-drop and progress
function MediaUploader({ type = "video", onUpload, courseId, lessonId, accept }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);

  const acceptTypes = {
    video: ".mp4,.mov,.avi,.webm",
    pdf: ".pdf",
    image: ".jpg,.jpeg,.png,.webp,.gif",
  };

  const maxSizes = { video: "2GB", pdf: "50MB", image: "10MB" };

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setIsDragging(true);
    else if (e.type === "dragleave") setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) uploadFile(files[0]);
  }, []);

  const handleSelect = (e) => {
    const files = e.target.files;
    if (files && files[0]) uploadFile(files[0]);
  };

  const uploadFile = async (file) => {
    setUploading(true);
    setProgress(0);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("upload_type", type);
    if (courseId) formData.append("course_id", courseId);
    if (lessonId) formData.append("lesson_id", lessonId);

    try {
      const res = await axios.post(`${API}/admin/media/upload`, formData, {
        withCredentials: true,
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded * 100) / e.total);
          setProgress(pct);
        },
      });
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} uploaded!`);
      onUpload?.(res.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
        isDragging ? "border-indigo-500 bg-indigo-50/50" : "border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50"
      }`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      data-testid={`media-uploader-${type}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept || acceptTypes[type]}
        onChange={handleSelect}
        className="hidden"
      />
      
      {uploading ? (
        <div className="space-y-3">
          <Loader2 className="w-8 h-8 text-indigo-500 mx-auto animate-spin" />
          <Progress value={progress} className="h-2 w-48 mx-auto" />
          <p className="text-xs text-slate-500 font-number">{progress}% uploaded</p>
        </div>
      ) : (
        <>
          <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-slate-100 flex items-center justify-center">
            {type === "video" ? <Video className="w-6 h-6 text-slate-400" /> :
             type === "pdf" ? <FileText className="w-6 h-6 text-slate-400" /> :
             <Image className="w-6 h-6 text-slate-400" />}
          </div>
          <p className="text-sm font-medium text-slate-700 mb-1">
            Drop {type} here or <span className="text-indigo-600">browse</span>
          </p>
          <p className="text-[10px] text-slate-400">
            Max size: {maxSizes[type]} &bull; {acceptTypes[type].replace(/\./g, "").toUpperCase()}
          </p>
        </>
      )}
    </div>
  );
}

// Commission Settings Component
function CommissionSettings() {
  const [settings, setSettings] = useState(null);
  
  useEffect(() => {
    axios.get(`${API}/admin/commission-settings`, { withCredentials: true })
      .then(res => setSettings(res.data))
      .catch(console.error);
  }, []);

  if (!settings) return <div className="text-center py-8"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>;

  const levelColors = ["#4f46e5", "#7c3aed", "#a855f7", "#ec4899", "#f97316"];

  return (
    <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
      <h3 className="font-heading font-semibold text-slate-900 mb-4 flex items-center gap-2">
        <BarChart3 className="w-4 h-4 text-indigo-500" /> Commission Structure (5 Levels)
      </h3>
      
      <div className="space-y-3 mb-5">
        {settings.levels.map((level, idx) => (
          <div key={level.level} className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ backgroundColor: levelColors[idx] }}>
              L{level.level}
            </div>
            <div className="flex-1">
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full rounded-full" style={{ width: `${level.percentage}%`, backgroundColor: levelColors[idx] }} />
              </div>
            </div>
            <span className="font-number text-sm font-bold text-slate-700 w-12 text-right">{level.percentage}%</span>
          </div>
        ))}
      </div>
      
      <div className="grid grid-cols-3 gap-3 text-center pt-4 border-t border-slate-100">
        <div>
          <p className="text-[10px] text-slate-400 uppercase">Total Payout</p>
          <p className="font-number text-lg font-bold text-indigo-600">{settings.total_payout_percent}%</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 uppercase">Platform Keeps</p>
          <p className="font-number text-lg font-bold text-emerald-600">{settings.platform_keep_percent}%</p>
        </div>
        <div>
          <p className="text-[10px] text-slate-400 uppercase">Min Withdrawal</p>
          <p className="font-number text-lg font-bold text-slate-700">₹{settings.min_withdrawal}</p>
        </div>
      </div>
    </Card>
  );
}

// Media Library Component
function MediaLibrary() {
  const [media, setMedia] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchMedia(); }, [filter]);

  const fetchMedia = async () => {
    setLoading(true);
    try {
      const params = filter !== "all" ? `?upload_type=${filter}` : "";
      const res = await axios.get(`${API}/admin/media${params}`, { withCredentials: true });
      setMedia(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const deleteMedia = async (mediaId) => {
    if (!window.confirm("Delete this file?")) return;
    try {
      await axios.delete(`${API}/admin/media/${mediaId}`, { withCredentials: true });
      toast.success("File deleted");
      fetchMedia();
    } catch (e) { toast.error("Delete failed"); }
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  const iconMap = { video: Video, pdf: FileText, image: Image };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-32 h-9 text-xs"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Files</SelectItem>
            <SelectItem value="video">Videos</SelectItem>
            <SelectItem value="pdf">PDFs</SelectItem>
            <SelectItem value="image">Images</SelectItem>
          </SelectContent>
        </Select>
        <span className="text-xs text-slate-400">{media.length} files</span>
      </div>

      {loading ? (
        <div className="text-center py-10"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>
      ) : media.length === 0 ? (
        <Card className="bg-slate-50 rounded-xl border border-dashed border-slate-200 p-10 text-center">
          <File className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-400 text-sm">No files uploaded yet</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {media.map((m) => {
            const Icon = iconMap[m.file_type] || File;
            return (
              <Card key={m.media_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-3 flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  m.file_type === "video" ? "bg-purple-50" : m.file_type === "pdf" ? "bg-red-50" : "bg-blue-50"
                }`}>
                  <Icon className={`w-5 h-5 ${
                    m.file_type === "video" ? "text-purple-500" : m.file_type === "pdf" ? "text-red-500" : "text-blue-500"
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-slate-700 truncate">{m.file_name}</p>
                  <p className="text-[10px] text-slate-400">
                    {formatSize(m.file_size)} &bull; {new Date(m.created_at).toLocaleDateString()}
                    {m.download_count > 0 && <> &bull; {m.download_count} downloads</>}
                  </p>
                </div>
                <Badge className={`${m.status === "ready" ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"} border-0 text-[10px]`}>
                  {m.status}
                </Badge>
                <Button variant="ghost" size="sm" onClick={() => deleteMedia(m.media_id)} className="text-red-400 hover:text-red-600 h-7 w-7 p-0">
                  <Trash2 className="w-3.5 h-3.5" />
                </Button>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Quiz Manager Component
function QuizManager({ courses }) {
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editOpen, setEditOpen] = useState(false);
  const [editingQuiz, setEditingQuiz] = useState(null);
  const [saving, setSaving] = useState(false);

  const emptyQuiz = {
    title: "", course_id: "", questions: [], passing_score: 70,
    is_timed: false, time_limit: 10, published: true,
  };

  const emptyQuestion = () => ({
    question_id: `q_${Date.now().toString(36)}`,
    question: "", options: ["", "", "", ""], correct_answer: "", explanation: "",
  });

  useEffect(() => { fetchQuizzes(); }, []);

  const fetchQuizzes = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/quizzes`, { withCredentials: true });
      setQuizzes(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  const openNew = () => { setEditingQuiz({ ...emptyQuiz, questions: [emptyQuestion()] }); setEditOpen(true); };

  const openEdit = async (quiz) => {
    try {
      const res = await axios.get(`${API}/admin/quizzes/${quiz.quiz_id}`, { withCredentials: true });
      setEditingQuiz(res.data);
      setEditOpen(true);
    } catch (e) { toast.error("Failed to load quiz"); }
  };

  const saveQuiz = async () => {
    if (!editingQuiz.title) { toast.error("Title is required"); return; }
    if (!editingQuiz.course_id) { toast.error("Select a course"); return; }
    if (!editingQuiz.questions?.length) { toast.error("Add at least one question"); return; }

    // Validate questions
    for (let i = 0; i < editingQuiz.questions.length; i++) {
      const q = editingQuiz.questions[i];
      if (!q.question) { toast.error(`Question ${i + 1}: text is required`); return; }
      const filledOptions = q.options.filter(o => o.trim());
      if (filledOptions.length < 2) { toast.error(`Question ${i + 1}: at least 2 options needed`); return; }
      if (!q.correct_answer) { toast.error(`Question ${i + 1}: select correct answer`); return; }
    }

    setSaving(true);
    try {
      // Clean empty options
      const payload = {
        ...editingQuiz,
        questions: editingQuiz.questions.map(q => ({
          ...q,
          options: q.options.filter(o => o.trim()),
        })),
      };
      if (editingQuiz.quiz_id) {
        await axios.put(`${API}/admin/quizzes/${editingQuiz.quiz_id}`, payload, { withCredentials: true });
        toast.success("Quiz updated!");
      } else {
        await axios.post(`${API}/admin/quizzes`, payload, { withCredentials: true });
        toast.success("Quiz created!");
      }
      setEditOpen(false);
      fetchQuizzes();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Save failed");
    } finally { setSaving(false); }
  };

  const deleteQuiz = async (quizId) => {
    if (!window.confirm("Delete this quiz and all attempts?")) return;
    try {
      await axios.delete(`${API}/admin/quizzes/${quizId}`, { withCredentials: true });
      toast.success("Quiz deleted");
      fetchQuizzes();
    } catch (e) { toast.error("Delete failed"); }
  };

  const updateQuestion = (idx, field, value) => {
    setEditingQuiz(prev => {
      const questions = [...prev.questions];
      questions[idx] = { ...questions[idx], [field]: value };
      return { ...prev, questions };
    });
  };

  const updateOption = (qIdx, oIdx, value) => {
    setEditingQuiz(prev => {
      const questions = [...prev.questions];
      const options = [...questions[qIdx].options];
      options[oIdx] = value;
      questions[qIdx] = { ...questions[qIdx], options };
      return { ...prev, questions };
    });
  };

  const addQuestion = () => {
    setEditingQuiz(prev => ({ ...prev, questions: [...prev.questions, emptyQuestion()] }));
  };

  const removeQuestion = (idx) => {
    setEditingQuiz(prev => ({ ...prev, questions: prev.questions.filter((_, i) => i !== idx) }));
  };

  const addOption = (qIdx) => {
    setEditingQuiz(prev => {
      const questions = [...prev.questions];
      questions[qIdx] = { ...questions[qIdx], options: [...questions[qIdx].options, ""] };
      return { ...prev, questions };
    });
  };

  const removeOption = (qIdx, oIdx) => {
    setEditingQuiz(prev => {
      const questions = [...prev.questions];
      const opts = questions[qIdx].options.filter((_, i) => i !== oIdx);
      const newQ = { ...questions[qIdx], options: opts };
      if (newQ.correct_answer === questions[qIdx].options[oIdx]) newQ.correct_answer = "";
      questions[qIdx] = newQ;
      return { ...prev, questions };
    });
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <Button onClick={openNew} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-5 text-xs font-semibold" data-testid="create-quiz-btn">
          <Plus className="w-4 h-4 mr-1" /> New Quiz
        </Button>
      </div>

      {loading ? (
        <div className="text-center py-10"><Loader2 className="w-6 h-6 animate-spin mx-auto text-slate-400" /></div>
      ) : quizzes.length === 0 ? (
        <Card className="bg-slate-50 rounded-xl border border-dashed border-slate-200 p-10 text-center">
          <ClipboardList className="w-10 h-10 text-slate-300 mx-auto mb-2" />
          <p className="text-slate-400 text-sm">No quizzes created yet</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {quizzes.map((q, idx) => (
            <Card key={q.quiz_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-4" data-testid={`quiz-row-${idx}`}>
              <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                <ClipboardList className="w-5 h-5 text-purple-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="font-heading font-semibold text-slate-900 text-sm truncate">{q.title}</h3>
                  {!q.published && <Badge className="bg-slate-100 text-slate-500 border-0 text-[10px]">Draft</Badge>}
                  {q.is_timed && <Badge className="bg-blue-50 text-blue-600 border-0 text-[10px]"><Clock className="w-2.5 h-2.5 mr-0.5 inline" />{q.time_limit}m</Badge>}
                </div>
                <p className="text-xs text-slate-400 font-body">{q.course_title} &middot; {q.question_count} questions &middot; Pass: {q.passing_score}%</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Button variant="outline" size="sm" onClick={() => openEdit(q)} className="text-xs rounded-lg h-8" data-testid={`edit-quiz-btn-${idx}`}>Edit</Button>
                <Button variant="ghost" size="sm" onClick={() => deleteQuiz(q.quiz_id)} className="text-red-500 hover:text-red-700 hover:bg-red-50 h-8 w-8 p-0">
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Quiz Editor Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">{editingQuiz?.quiz_id ? "Edit Quiz" : "Create Quiz"}</DialogTitle>
          </DialogHeader>

          {editingQuiz && (
            <div className="space-y-4 py-2">
              {/* Quiz Metadata */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs font-body">Quiz Title</Label>
                  <Input value={editingQuiz.title} onChange={e => setEditingQuiz({ ...editingQuiz, title: e.target.value })} className="mt-1" placeholder="e.g. Chapter 1 Assessment" data-testid="quiz-title-input" />
                </div>
                <div>
                  <Label className="text-xs font-body">Course</Label>
                  <Select value={editingQuiz.course_id} onValueChange={v => setEditingQuiz({ ...editingQuiz, course_id: v })}>
                    <SelectTrigger className="mt-1" data-testid="quiz-course-select"><SelectValue placeholder="Select course" /></SelectTrigger>
                    <SelectContent>
                      {courses.map(c => (
                        <SelectItem key={c.course_id} value={c.course_id}>{c.title}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <Label className="text-xs font-body">Pass Threshold (%)</Label>
                  <Input type="number" min={0} max={100} value={editingQuiz.passing_score} onChange={e => setEditingQuiz({ ...editingQuiz, passing_score: parseInt(e.target.value) || 0 })} className="mt-1 font-number" data-testid="quiz-pass-input" />
                </div>
                <div className="flex items-end gap-3">
                  <div className="flex items-center gap-2">
                    <Switch checked={editingQuiz.is_timed} onCheckedChange={v => setEditingQuiz({ ...editingQuiz, is_timed: v })} />
                    <Label className="text-xs font-body">Timed</Label>
                  </div>
                  {editingQuiz.is_timed && (
                    <div className="flex-1">
                      <Input type="number" min={1} value={editingQuiz.time_limit || ""} onChange={e => setEditingQuiz({ ...editingQuiz, time_limit: parseInt(e.target.value) || null })} className="font-number h-9" placeholder="min" />
                    </div>
                  )}
                </div>
                <div className="flex items-end">
                  <div className="flex items-center gap-2">
                    <Switch checked={editingQuiz.published} onCheckedChange={v => setEditingQuiz({ ...editingQuiz, published: v })} />
                    <Label className="text-xs font-body">Published</Label>
                  </div>
                </div>
              </div>

              {/* Questions */}
              <div className="border-t border-slate-100 pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-heading font-semibold text-sm text-slate-900 flex items-center gap-1.5">
                    <ClipboardList className="w-4 h-4 text-purple-500" /> Questions ({editingQuiz.questions?.length || 0})
                  </h3>
                  <Button variant="outline" size="sm" onClick={addQuestion} className="text-xs rounded-lg h-7" data-testid="add-question-btn">
                    <Plus className="w-3 h-3 mr-1" /> Add Question
                  </Button>
                </div>
                <div className="space-y-4">
                  {editingQuiz.questions?.map((q, qi) => (
                    <Card key={q.question_id || qi} className="bg-slate-50 rounded-lg p-4 border border-slate-100" data-testid={`question-card-${qi}`}>
                      <div className="flex items-start gap-2 mb-3">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-xs font-bold shrink-0 mt-1">{qi + 1}</span>
                        <div className="flex-1">
                          <Input placeholder="Question text" value={q.question} onChange={e => updateQuestion(qi, "question", e.target.value)} className="text-sm font-medium" data-testid={`question-text-${qi}`} />
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeQuestion(qi)} className="text-red-400 h-8 w-8 p-0 shrink-0"><Trash2 className="w-3.5 h-3.5" /></Button>
                      </div>

                      {/* Options */}
                      <div className="ml-8 space-y-2 mb-3">
                        <p className="text-[10px] text-slate-400 uppercase tracking-wider">Options (click radio to set correct answer)</p>
                        {q.options.map((opt, oi) => (
                          <div key={oi} className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => updateQuestion(qi, "correct_answer", opt)}
                              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
                                opt && q.correct_answer === opt
                                  ? "border-emerald-500 bg-emerald-500"
                                  : "border-slate-300 hover:border-slate-400"
                              }`}
                              data-testid={`option-radio-${qi}-${oi}`}
                            >
                              {opt && q.correct_answer === opt && <Check className="w-3 h-3 text-white" />}
                            </button>
                            <Input
                              placeholder={`Option ${String.fromCharCode(65 + oi)}`}
                              value={opt}
                              onChange={e => {
                                const newVal = e.target.value;
                                if (q.correct_answer === opt) updateQuestion(qi, "correct_answer", newVal);
                                updateOption(qi, oi, newVal);
                              }}
                              className="text-xs h-8 flex-1"
                              data-testid={`option-input-${qi}-${oi}`}
                            />
                            {q.options.length > 2 && (
                              <Button variant="ghost" size="sm" onClick={() => removeOption(qi, oi)} className="text-slate-400 h-7 w-7 p-0"><X className="w-3 h-3" /></Button>
                            )}
                          </div>
                        ))}
                        {q.options.length < 6 && (
                          <Button variant="ghost" size="sm" onClick={() => addOption(qi)} className="text-xs text-indigo-600 h-7 pl-7">
                            <Plus className="w-3 h-3 mr-1" /> Add Option
                          </Button>
                        )}
                      </div>

                      {/* Explanation */}
                      <div className="ml-8">
                        <Input placeholder="Explanation (shown after answering, optional)" value={q.explanation || ""} onChange={e => updateQuestion(qi, "explanation", e.target.value)} className="text-xs h-8 text-slate-500" data-testid={`question-explanation-${qi}`} />
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditOpen(false)} className="rounded-full text-xs">Cancel</Button>
            <Button onClick={saveQuiz} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs" data-testid="save-quiz-btn">
              {saving ? "Saving..." : <><Save className="w-3.5 h-3.5 mr-1" /> Save Quiz</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function AdminCourses() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [categories, setCategories] = useState([]);
  const [adminStats, setAdminStats] = useState(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState("courses");

  const emptyCourse = {
    title: "", description: "", price: 500, original_price: 999,
    image: "", category: "", tier: "standard",
    is_upsell: false, upsell_for: "", published: true,
    lessons: [], resources: [],
  };

  useEffect(() => {
    if (!user?.is_admin) return;
    fetchCourses();
    fetchStats();
    fetchCategories();
  }, [user]);

  const fetchCourses = async () => {
    try {
      const res = await axios.get(`${API}/admin/courses`, { withCredentials: true });
      setCourses(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchCategories = async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data);
    } catch (e) { toast.error("Couldn't load categories. You can still enter a category name."); }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/admin/stats`, { withCredentials: true });
      setAdminStats(res.data);
    } catch (e) { console.error(e); }
  };

  const openNew = () => { setEditingCourse({ ...emptyCourse }); fetchCategories(); setEditOpen(true); };
  const openEdit = async (course) => {
    fetchCategories();
    try {
      const res = await axios.get(`${API}/courses/${course.course_id}`);
      const fullCourse = res.data;
      // Preserve media_id for resources that have a url (so the uploader shows "uploaded" state)
      const resources = (fullCourse.resources || []).map((r) => ({
        ...r,
        media_id: r.url ? "existing" : null,
      }));
      setEditingCourse({ ...fullCourse, resources });
      setEditOpen(true);
    } catch (e) {
      console.error("Failed to fetch course detail for edit", e);
      // Fallback to list data
      setEditingCourse({ ...course, resources: course.resources || [], lessons: course.lessons || [] });
      setEditOpen(true);
    }
  };

  const addLesson = () => {
    setEditingCourse((prev) => ({
      ...prev,
      lessons: [...(prev.lessons || []), { title: "", description: "", video_url: "", video_type: "youtube", duration: "", is_free_preview: false }],
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

  const handleLessonVideoUpload = (idx, mediaData) => {
    setEditingCourse((prev) => {
      const lessons = [...prev.lessons];
      lessons[idx] = {
        ...lessons[idx],
        video_type: "upload",
        video_url: mediaData.url,
        media_id: mediaData.media_id,
      };
      return { ...prev, lessons };
    });
  };

  const addResource = () => {
    setEditingCourse((prev) => ({
      ...prev,
      resources: [...(prev.resources || []), { name: "", type: "pdf", url: "", is_free_preview: false }],
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

  const handleResourceUpload = (idx, mediaData) => {
    setEditingCourse((prev) => {
      const resources = [...prev.resources];
      resources[idx] = {
        ...resources[idx],
        url: mediaData.url,
        name: resources[idx].name || mediaData.file_name,
        media_id: mediaData.media_id,
      };
      return { ...prev, resources };
    });
  };

  const saveCourse = async () => {
    if (!editingCourse.title?.trim()) { toast.error("Title is required"); return; }
    if (!editingCourse.category?.trim()) { toast.error("Choose or enter a category"); return; }
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
      fetchCategories();
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
          <p className="text-slate-400 font-body text-sm">Manage courses, media and platform settings</p>
        </div>
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

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-slate-100/60 p-1 rounded-full inline-flex flex-wrap h-auto mb-5">
          <TabsTrigger value="courses" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium">
            Courses ({courses.length})
          </TabsTrigger>
          <TabsTrigger value="quizzes" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-purple-600 data-[state=active]:shadow-sm text-xs font-medium">
            Quizzes
          </TabsTrigger>
          <TabsTrigger value="media" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium">
            Media Library
          </TabsTrigger>
          <TabsTrigger value="settings" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-indigo-600 data-[state=active]:shadow-sm text-xs font-medium">
            Settings
          </TabsTrigger>
          <TabsTrigger value="landing" data-testid="admin-landing-tab" className="rounded-full px-4 py-1.5 data-[state=active]:bg-white data-[state=active]:text-orange-700 text-xs font-medium">Landing page</TabsTrigger>
        </TabsList>

        <TabsContent value="courses">
          <div className="flex justify-end mb-4">
            <Button data-testid="create-course-btn" onClick={openNew} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-5 text-xs font-semibold">
              <Plus className="w-4 h-4 mr-1" /> New Course
            </Button>
          </div>

          {/* Course List */}
          <div className="space-y-3">
            {courses.map((course, idx) => (
              <Card key={course.course_id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 flex items-center gap-4" data-testid={`admin-course-row-${idx}`}>
                {course.image ? <img src={course.image} alt={course.title} className="w-16 h-12 rounded-lg object-cover shrink-0" /> : <div className="w-16 h-12 rounded-lg bg-orange-100 grid place-items-center shrink-0"><BarChart3 className="text-orange-600 w-6 h-6" /></div>}
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
        </TabsContent>

        <TabsContent value="quizzes">
          <QuizManager courses={courses} />
        </TabsContent>

        <TabsContent value="media">
          <div className="grid md:grid-cols-3 gap-5 mb-6">
            <MediaUploader type="video" onUpload={() => {}} />
            <MediaUploader type="pdf" onUpload={() => {}} />
            <MediaUploader type="image" onUpload={() => {}} />
          </div>
          <MediaLibrary />
        </TabsContent>

        <TabsContent value="landing"><LandingManager courses={courses} /></TabsContent>
        <TabsContent value="settings">
          <div className="grid md:grid-cols-2 gap-5 mb-5">
            <CommissionSettings />
            <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
              <h3 className="font-heading font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Settings className="w-4 h-4 text-indigo-500" /> Storage Configuration
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-700">Storage Mode</p>
                    <p className="text-[10px] text-slate-400">Currently using mock storage (local files)</p>
                  </div>
                  <Badge className="bg-amber-100 text-amber-700 border-0">Mock</Badge>
                </div>
                <p className="text-xs text-slate-500">
                  To enable cloud storage, provide R2/S3 credentials in environment variables.
                  Files are currently stored locally and will need to be re-uploaded after switching to cloud.
                </p>
              </div>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Edit/Create Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent data-testid="course-editor-dialog" className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-heading">{editingCourse?.course_id ? "Edit Course" : "Create Course"}</DialogTitle>
            <DialogDescription className="sr-only">Course details, category, lessons and resources.</DialogDescription>
          </DialogHeader>

          {editingCourse && (
            <div className="space-y-4 py-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs font-body">Title</Label>
                  <Input data-testid="course-title-input" value={editingCourse.title} onChange={(e) => setEditingCourse({ ...editingCourse, title: e.target.value })} className="mt-1" />
                </div>
                <div>
                  <Label htmlFor="course-category" className="text-xs font-body">Category</Label>
                  <Input id="course-category" data-testid="course-category-input" list="course-category-options"
                    value={editingCourse.category || ""} maxLength={100} autoComplete="off"
                    onChange={(e) => setEditingCourse({ ...editingCourse, category: e.target.value })}
                    className="mt-1" placeholder="Select or type a category" />
                  <datalist id="course-category-options" data-testid="course-category-options">
                    {categories.map((category, index) => <option key={category.name} value={category.name} data-testid={`course-category-option-${index}`} />)}
                  </datalist>
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
                          
                          {/* Video Source Toggle */}
                          <div className="flex items-center gap-2 mb-2">
                            <Button
                              type="button"
                              variant={lesson.video_type !== "upload" ? "default" : "outline"}
                              size="sm"
                              onClick={() => updateLesson(idx, "video_type", "youtube")}
                              className="text-[10px] h-6 px-2 rounded"
                            >
                              <Youtube className="w-3 h-3 mr-1" /> YouTube
                            </Button>
                            <Button
                              type="button"
                              variant={lesson.video_type === "upload" ? "default" : "outline"}
                              size="sm"
                              onClick={() => updateLesson(idx, "video_type", "upload")}
                              className="text-[10px] h-6 px-2 rounded"
                            >
                              <Upload className="w-3 h-3 mr-1" /> Upload
                            </Button>
                            <div className="flex items-center gap-1 ml-auto">
                              <Switch
                                checked={lesson.is_free_preview}
                                onCheckedChange={(v) => updateLesson(idx, "is_free_preview", v)}
                                className="scale-75"
                              />
                              <span className="text-[10px] text-slate-500">Free Preview</span>
                            </div>
                          </div>

                          {lesson.video_type === "upload" ? (
                            lesson.media_id ? (
                              <div className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg border border-emerald-200">
                                <Check className="w-4 h-4 text-emerald-600" />
                                <span className="text-xs text-emerald-700">Video uploaded</span>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => updateLesson(idx, "media_id", null)}
                                  className="text-red-400 h-6 w-6 p-0 ml-auto"
                                >
                                  <X className="w-3 h-3" />
                                </Button>
                              </div>
                            ) : (
                              <MediaUploader
                                type="video"
                                courseId={editingCourse.course_id}
                                onUpload={(data) => handleLessonVideoUpload(idx, data)}
                              />
                            )
                          ) : (
                            <Input placeholder="YouTube embed URL (youtube-nocookie.com)" value={lesson.video_url} onChange={(e) => updateLesson(idx, "video_url", e.target.value)} className="text-xs h-8" />
                          )}

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
                <div className="space-y-3">
                  {editingCourse.resources?.map((res, idx) => (
                    <Card key={idx} className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                      <div className="flex items-center gap-2 mb-2">
                        <Input placeholder="Resource name" value={res.name} onChange={(e) => updateResource(idx, "name", e.target.value)} className="text-xs h-8 flex-1" />
                        <Select value={res.type} onValueChange={(v) => updateResource(idx, "type", v)}>
                          <SelectTrigger className="w-20 h-8 text-xs"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pdf">PDF</SelectItem>
                            <SelectItem value="doc">DOC</SelectItem>
                            <SelectItem value="link">Link</SelectItem>
                          </SelectContent>
                        </Select>
                        <div className="flex items-center gap-1">
                          <Switch
                            checked={res.is_free_preview}
                            onCheckedChange={(v) => updateResource(idx, "is_free_preview", v)}
                            className="scale-75"
                          />
                          <span className="text-[10px] text-slate-500">Free</span>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => removeResource(idx)} className="text-red-400 h-8 w-8 p-0"><Trash2 className="w-3.5 h-3.5" /></Button>
                      </div>
                      
                      {res.type === "pdf" ? (
                        res.media_id ? (
                          <div className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg border border-emerald-200">
                            <Check className="w-4 h-4 text-emerald-600" />
                            <span className="text-xs text-emerald-700 truncate flex-1">{res.name || "PDF uploaded"}</span>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => updateResource(idx, "media_id", null)}
                              className="text-red-400 h-6 w-6 p-0"
                            >
                              <X className="w-3 h-3" />
                            </Button>
                          </div>
                        ) : (
                          <MediaUploader
                            type="pdf"
                            courseId={editingCourse.course_id}
                            onUpload={(data) => handleResourceUpload(idx, data)}
                          />
                        )
                      ) : (
                        <Input placeholder="URL" value={res.url} onChange={(e) => updateResource(idx, "url", e.target.value)} className="text-xs h-8" />
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button data-testid="cancel-course-btn" variant="outline" onClick={() => setEditOpen(false)} className="rounded-full text-xs">Cancel</Button>
            <Button data-testid="save-course-btn" onClick={saveCourse} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs">
              {saving ? "Saving..." : <><Save className="w-3.5 h-3.5 mr-1" /> Save Course</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
