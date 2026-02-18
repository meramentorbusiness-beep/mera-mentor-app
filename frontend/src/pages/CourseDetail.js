import { useState, useEffect } from "react";
import { useAuth, API } from "@/App";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Play, FileText, Lock, ChevronRight, ArrowLeft, CheckCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

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

  useEffect(() => {
    fetchCourse();
    fetchLessons();
  }, [courseId]);

  const fetchCourse = async () => {
    try {
      const res = await axios.get(`${API}/courses/${courseId}`);
      setCourse(res.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fetchLessons = async () => {
    try {
      const res = await axios.get(`${API}/courses/${courseId}/lessons`, { withCredentials: true });
      setLessons(res.data.lessons || []);
      setResources(res.data.resources || []);
      setHasAccess(true);
      if (res.data.lessons?.length > 0) setActiveLesson(res.data.lessons[0]);
    } catch (e) {
      setHasAccess(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><div className="loader"></div></div>;
  if (!course) return <div className="text-center py-20"><p className="text-slate-500">Course not found</p></div>;

  return (
    <div className="animate-slide-up" data-testid="course-detail-page">
      {/* Back button */}
      <button onClick={() => navigate("/courses")} className="flex items-center gap-1.5 text-slate-500 hover:text-slate-700 text-sm font-body mb-4 transition-colors" data-testid="back-to-courses">
        <ArrowLeft className="w-4 h-4" /> Back to Courses
      </button>

      {hasAccess ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Player */}
          <div className="lg:col-span-2">
            {activeLesson?.video_url ? (
              <div className="video-wrapper rounded-xl overflow-hidden bg-black aspect-video mb-4" onContextMenu={(e) => e.preventDefault()}>
                <iframe
                  src={activeLesson.video_url}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  referrerPolicy="no-referrer"
                  sandbox="allow-scripts allow-same-origin allow-presentation"
                  title={activeLesson.title}
                  data-testid="video-player"
                />
              </div>
            ) : (
              <div className="rounded-xl bg-slate-100 aspect-video flex items-center justify-center mb-4">
                <p className="text-slate-400 font-body">No video available</p>
              </div>
            )}

            <h2 className="font-heading text-xl font-bold text-slate-900 mb-1" data-testid="active-lesson-title">
              {activeLesson?.title || course.title}
            </h2>
            <p className="text-sm text-slate-500 font-body mb-4">{activeLesson?.description || course.description}</p>

            {/* Resources */}
            {resources.length > 0 && (
              <Card className="bg-white rounded-xl border border-slate-100 p-4">
                <h3 className="font-heading font-semibold text-slate-800 text-sm mb-3">Course Resources</h3>
                <div className="space-y-2">
                  {resources.map((r, i) => (
                    <div key={i} className="flex items-center gap-3 p-2.5 bg-slate-50 rounded-lg">
                      <FileText className="w-4 h-4 text-indigo-500" />
                      <span className="text-sm font-body text-slate-700 flex-1">{r.name}</span>
                      <Badge className="bg-indigo-50 text-indigo-600 border-0 text-[10px] uppercase">{r.type}</Badge>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </div>

          {/* Lesson Sidebar */}
          <div className="lg:col-span-1">
            <Card className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden sticky top-20">
              <div className="p-4 border-b border-slate-100">
                <h3 className="font-heading font-semibold text-slate-900 text-sm">{course.title}</h3>
                <p className="text-xs text-slate-400 font-body mt-0.5">{lessons.length} lessons</p>
              </div>
              <div className="max-h-[60vh] overflow-y-auto">
                {lessons.map((lesson, idx) => (
                  <button
                    key={lesson.lesson_id}
                    onClick={() => setActiveLesson(lesson)}
                    data-testid={`lesson-item-${idx}`}
                    className={`w-full text-left p-3.5 flex items-center gap-3 border-b border-slate-50 transition-colors ${
                      activeLesson?.lesson_id === lesson.lesson_id ? "bg-indigo-50" : "hover:bg-slate-50"
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold font-number ${
                      activeLesson?.lesson_id === lesson.lesson_id ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-500"
                    }`}>
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-medium truncate ${activeLesson?.lesson_id === lesson.lesson_id ? "text-indigo-700" : "text-slate-700"}`}>
                        {lesson.title}
                      </p>
                      {lesson.duration && <p className="text-[10px] text-slate-400 font-number">{lesson.duration}</p>}
                    </div>
                    {activeLesson?.lesson_id === lesson.lesson_id && <Play className="w-3.5 h-3.5 text-indigo-600 shrink-0" />}
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>
      ) : (
        /* Locked state */
        <Card className="bg-white rounded-xl border border-slate-100 shadow-sm p-10 text-center max-w-lg mx-auto">
          <div className="w-16 h-16 rounded-full bg-slate-100 mx-auto mb-4 flex items-center justify-center">
            <Lock className="w-8 h-8 text-slate-400" />
          </div>
          <h2 className="font-heading text-xl font-bold text-slate-900 mb-2">{course.title}</h2>
          <p className="text-sm text-slate-500 font-body mb-6">{course.description}</p>
          <p className="text-slate-400 font-body text-sm mb-4">Purchase this course to access all lessons and resources</p>
          <Button onClick={() => navigate("/courses")} className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-full px-8 py-5 font-semibold" data-testid="go-to-courses-btn">
            Go to Courses
          </Button>
        </Card>
      )}
    </div>
  );
}
