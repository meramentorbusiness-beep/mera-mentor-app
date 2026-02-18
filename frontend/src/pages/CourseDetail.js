import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "sonner";
import { Play, FileText, Lock, ArrowLeft, CheckCircle, Circle, Star, Send } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";

export default function CourseDetail() {
  const { courseId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [resources, setResources] = useState([]);
  const [activeLesson, setActiveLesson] = useState(null);
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const [progressCount, setProgressCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [quizzes, setQuizzes] = useState([]);
  const [activeQuiz, setActiveQuiz] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [quizResult, setQuizResult] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [newReview, setNewReview] = useState({ rating: 5, comment: "" });
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [tab, setTab] = useState("lessons");

  useEffect(() => {
    fetchCourse();
    fetchLessons();
    fetchReviews();
  }, [courseId]);

  const fetchCourse = async () => {
    try { const res = await axios.get(`${API}/courses/${courseId}`); setCourse(res.data); } catch {} setLoading(false);
  };
  const fetchLessons = async () => {
    try {
      const res = await axios.get(`${API}/courses/${courseId}/lessons`, { withCredentials: true });
      setLessons(res.data.lessons || []); setResources(res.data.resources || []);
      setQuizzes(res.data.quizzes || []);
      setProgressCount(res.data.progress_count); setTotalCount(res.data.total_count);
      setHasAccess(true);
      if (res.data.lessons?.length > 0) {
        const firstIncomplete = res.data.lessons.find(l => !l.completed) || res.data.lessons[0];
        setActiveLesson(firstIncomplete);
      }
    } catch { setHasAccess(false); }
  };
  const fetchReviews = async () => {
    try { const res = await axios.get(`${API}/reviews/${courseId}`); setReviews(res.data); } catch {}
  };

  const markComplete = async () => {
    if (!activeLesson) return;
    try {
      const res = await axios.post(`${API}/progress/complete`, { course_id: courseId, lesson_id: activeLesson.lesson_id }, { withCredentials: true });
      toast.success("Lesson completed! +" + "10 XP");
      setProgressCount(res.data.completed);
      setLessons(prev => prev.map(l => l.lesson_id === activeLesson.lesson_id ? { ...l, completed: true } : l));
      if (res.data.completed >= res.data.total) toast.success("Course completed! Certificate earned!");
    } catch (e) { toast.info(e.response?.data?.message || "Already completed"); }
  };

  const submitQuiz = async () => {
    if (!activeQuiz) return;
    try {
      const res = await axios.post(`${API}/quizzes/${activeQuiz.quiz_id}/submit`, { answers: quizAnswers }, { withCredentials: true });
      setQuizResult(res.data);
      if (res.data.passed) toast.success(`Quiz passed! Score: ${res.data.score}%`);
      else toast.error(`Score: ${res.data.score}%. Need ${res.data.pass_percentage}% to pass.`);
    } catch (e) { toast.error("Submit failed"); }
  };

  const submitReview = async () => {
    try {
      await axios.post(`${API}/reviews`, { course_id: courseId, rating: newReview.rating, comment: newReview.comment }, { withCredentials: true });
      toast.success("Review submitted!"); setShowReviewForm(false); fetchReviews();
    } catch (e) { toast.error(e.response?.data?.detail || "Review failed"); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><div className="loader"></div></div>;
  if (!course) return <div className="text-center py-20"><p className="text-slate-500">Course not found</p></div>;

  const progressPct = totalCount > 0 ? Math.round((progressCount / totalCount) * 100) : 0;

  return (
    <div className="animate-slide-up" data-testid="course-detail-page">
      <button onClick={() => navigate("/courses")} className="flex items-center gap-1.5 text-slate-500 hover:text-slate-700 text-xs mb-4" data-testid="back-to-courses">
        <ArrowLeft className="w-3.5 h-3.5" /> Back
      </button>

      {hasAccess ? (
        <>
          {/* Progress bar */}
          <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 mb-4 flex items-center gap-4">
            <div className="flex-1">
              <div className="flex justify-between mb-1">
                <span className="text-xs font-heading font-semibold text-slate-800">{course.title}</span>
                <span className="text-[10px] font-number text-slate-500">{progressCount}/{totalCount} lessons</span>
              </div>
              <Progress value={progressPct} className="h-2" />
            </div>
            <span className="font-number text-sm font-bold text-indigo-600">{progressPct}%</span>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            {/* Main content */}
            <div className="lg:col-span-2">
              {/* Tab bar */}
              <div className="flex gap-1 mb-4 bg-slate-100/60 p-1 rounded-full inline-flex">
                {["lessons", "quizzes", "reviews"].map(t => (
                  <button key={t} onClick={() => setTab(t)}
                    className={`px-4 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${tab === t ? "bg-white text-indigo-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}>
                    {t}{t === "quizzes" && quizzes.length > 0 ? ` (${quizzes.length})` : t === "reviews" ? ` (${reviews.length})` : ""}
                  </button>
                ))}
              </div>

              {tab === "lessons" && (
                <>
                  {activeLesson?.video_url ? (
                    <div className="video-wrapper rounded-xl overflow-hidden bg-black aspect-video mb-4" onContextMenu={e => e.preventDefault()}>
                      <iframe src={activeLesson.video_url} className="w-full h-full" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen referrerPolicy="no-referrer" sandbox="allow-scripts allow-same-origin allow-presentation" title={activeLesson.title} data-testid="video-player" />
                    </div>
                  ) : (
                    <div className="rounded-xl bg-slate-100 aspect-video flex items-center justify-center mb-4"><p className="text-slate-400 text-sm">No video</p></div>
                  )}
                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div>
                      <h2 className="font-heading text-lg font-bold text-slate-900" data-testid="active-lesson-title">{activeLesson?.title}</h2>
                      <p className="text-xs text-slate-500 mt-0.5">{activeLesson?.description}</p>
                    </div>
                    {activeLesson && !activeLesson.completed && (
                      <Button onClick={markComplete} className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-full px-4 text-xs shrink-0" data-testid="mark-complete-btn">
                        <CheckCircle className="w-3.5 h-3.5 mr-1" /> Mark Complete
                      </Button>
                    )}
                    {activeLesson?.completed && (
                      <Badge className="bg-emerald-100 text-emerald-700 border-0 text-xs shrink-0">Completed</Badge>
                    )}
                  </div>
                  {resources.length > 0 && (
                    <Card className="bg-white rounded-xl border border-slate-100 p-4">
                      <h3 className="font-heading font-semibold text-xs text-slate-800 mb-2">Resources</h3>
                      <div className="space-y-1.5">
                        {resources.map((r, i) => (
                          <div key={i} className="flex items-center gap-2.5 p-2 bg-slate-50 rounded-lg">
                            <FileText className="w-3.5 h-3.5 text-indigo-500" />
                            <span className="text-xs text-slate-700 flex-1">{r.name}</span>
                            <Badge className="bg-indigo-50 text-indigo-600 border-0 text-[9px] uppercase">{r.type}</Badge>
                          </div>
                        ))}
                      </div>
                    </Card>
                  )}
                </>
              )}

              {tab === "quizzes" && (
                <div>
                  {activeQuiz ? (
                    <Card className="bg-white rounded-xl border border-slate-100 p-5">
                      <h3 className="font-heading font-bold text-base text-slate-900 mb-4">{activeQuiz.title}</h3>
                      {quizResult ? (
                        <div className="text-center py-6">
                          <div className={`w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center ${quizResult.passed ? "bg-emerald-50" : "bg-red-50"}`}>
                            <span className={`font-number text-2xl font-extrabold ${quizResult.passed ? "text-emerald-600" : "text-red-600"}`}>{quizResult.score}%</span>
                          </div>
                          <p className={`font-heading font-bold ${quizResult.passed ? "text-emerald-600" : "text-red-600"}`}>{quizResult.passed ? "Passed!" : "Not Passed"}</p>
                          <p className="text-xs text-slate-500 mt-1">{quizResult.correct}/{quizResult.total} correct. Need {quizResult.pass_percentage}% to pass.</p>
                          <Button onClick={() => { setActiveQuiz(null); setQuizResult(null); setQuizAnswers({}); }} className="mt-4 rounded-full text-xs" variant="outline">Back to Quizzes</Button>
                        </div>
                      ) : (
                        <div className="space-y-5">
                          {activeQuiz.questions?.map((q, qi) => (
                            <div key={q.question_id || qi}>
                              <p className="text-sm font-medium text-slate-800 mb-2">{qi + 1}. {q.question}</p>
                              <RadioGroup value={quizAnswers[q.question_id] || ""} onValueChange={(v) => setQuizAnswers(prev => ({ ...prev, [q.question_id]: v }))}>
                                {q.options?.map((opt, oi) => (
                                  <div key={oi} className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50">
                                    <RadioGroupItem value={opt} id={`${q.question_id}-${oi}`} />
                                    <Label htmlFor={`${q.question_id}-${oi}`} className="text-xs text-slate-700 cursor-pointer">{opt}</Label>
                                  </div>
                                ))}
                              </RadioGroup>
                            </div>
                          ))}
                          <Button onClick={submitQuiz} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-6 text-xs" data-testid="submit-quiz-btn">Submit Quiz</Button>
                        </div>
                      )}
                    </Card>
                  ) : (
                    <div className="space-y-3">
                      {quizzes.length === 0 ? (
                        <Card className="bg-white rounded-xl border border-slate-100 p-8 text-center"><p className="text-xs text-slate-400">No quizzes for this course yet</p></Card>
                      ) : quizzes.map((q, i) => (
                        <Card key={q.quiz_id} className="bg-white rounded-xl border border-slate-100 p-4 flex items-center gap-3 cursor-pointer hover:bg-slate-50" onClick={() => setActiveQuiz(q)} data-testid={`quiz-card-${i}`}>
                          <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center"><span className="font-number text-xs font-bold text-purple-600">Q{i + 1}</span></div>
                          <div className="flex-1"><p className="text-xs font-semibold text-slate-800">{q.title}</p><p className="text-[10px] text-slate-400">{q.questions?.length || 0} questions &middot; Pass: {q.pass_percentage}%</p></div>
                          {q.last_attempt && <Badge className={`${q.last_attempt.passed ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"} border-0 text-[10px]`}>{q.last_attempt.score}%</Badge>}
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {tab === "reviews" && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-heading font-semibold text-sm text-slate-900">Reviews ({reviews.length})</h3>
                    <Button onClick={() => setShowReviewForm(!showReviewForm)} variant="outline" className="rounded-full text-xs" data-testid="write-review-btn">
                      <Star className="w-3 h-3 mr-1" /> Write Review
                    </Button>
                  </div>
                  {showReviewForm && (
                    <Card className="bg-white rounded-xl border border-slate-100 p-4 mb-4">
                      <div className="flex items-center gap-1 mb-3">
                        {[1, 2, 3, 4, 5].map(s => (
                          <button key={s} onClick={() => setNewReview(p => ({ ...p, rating: s }))} className="p-0.5" data-testid={`star-${s}`}>
                            <Star className={`w-5 h-5 ${s <= newReview.rating ? "fill-amber-400 text-amber-400" : "text-slate-300"}`} />
                          </button>
                        ))}
                      </div>
                      <Textarea value={newReview.comment} onChange={e => setNewReview(p => ({ ...p, comment: e.target.value }))} placeholder="Share your experience..." className="text-xs mb-3" rows={3} data-testid="review-comment" />
                      <Button onClick={submitReview} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full text-xs px-5" data-testid="submit-review-btn"><Send className="w-3 h-3 mr-1" />Submit</Button>
                    </Card>
                  )}
                  <div className="space-y-2">
                    {reviews.map((r, i) => (
                      <Card key={r.review_id} className="bg-white rounded-xl border border-slate-100 p-3.5" data-testid={`review-${i}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-bold text-slate-600">{r.user_name?.[0]}</div>
                          <div className="flex-1"><p className="text-xs font-semibold text-slate-800">{r.user_name}</p></div>
                          <div className="flex items-center gap-0.5">
                            {[1, 2, 3, 4, 5].map(s => <Star key={s} className={`w-3 h-3 ${s <= r.rating ? "fill-amber-400 text-amber-400" : "text-slate-200"}`} />)}
                          </div>
                          {r.verified && <Badge className="bg-emerald-50 text-emerald-600 border-0 text-[9px]">Verified</Badge>}
                        </div>
                        {r.comment && <p className="text-xs text-slate-600 leading-relaxed">{r.comment}</p>}
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Lesson Sidebar */}
            <div className="lg:col-span-1">
              <Card className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden sticky top-20">
                <div className="p-3 border-b border-slate-100">
                  <h3 className="font-heading font-semibold text-xs text-slate-900">{course.title}</h3>
                  <p className="text-[10px] text-slate-400">{lessons.length} lessons &middot; {progressCount} done</p>
                </div>
                <div className="max-h-[55vh] overflow-y-auto">
                  {lessons.map((l, i) => (
                    <button key={l.lesson_id} onClick={() => { setActiveLesson(l); setTab("lessons"); }} data-testid={`lesson-item-${i}`}
                      className={`w-full text-left p-3 flex items-center gap-2.5 border-b border-slate-50 transition-colors ${activeLesson?.lesson_id === l.lesson_id ? "bg-indigo-50" : "hover:bg-slate-50"}`}>
                      {l.completed ? <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" /> : <Circle className={`w-4 h-4 shrink-0 ${activeLesson?.lesson_id === l.lesson_id ? "text-indigo-500" : "text-slate-300"}`} />}
                      <div className="flex-1 min-w-0">
                        <p className={`text-[11px] font-medium truncate ${activeLesson?.lesson_id === l.lesson_id ? "text-indigo-700" : l.completed ? "text-slate-500" : "text-slate-700"}`}>{l.title}</p>
                        {l.duration && <p className="text-[9px] text-slate-400">{l.duration}</p>}
                      </div>
                    </button>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </>
      ) : (
        <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center max-w-lg mx-auto">
          <Lock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <h2 className="font-heading text-lg font-bold text-slate-900 mb-1">{course.title}</h2>
          <p className="text-xs text-slate-500 mb-4">{course.description}</p>
          <Button onClick={() => navigate("/courses")} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-8 py-4 text-xs" data-testid="go-to-courses-btn">Go to Courses</Button>
        </Card>
      )}
    </div>
  );
}
