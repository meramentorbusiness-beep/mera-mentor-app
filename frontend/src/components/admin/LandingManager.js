import { useEffect, useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Plus, Save, Trash2, Pencil, ExternalLink, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LandingReviewEditor } from './LandingReviewEditor';

const API = `${process.env.REACT_APP_BACKEND_URL}/api/admin/landing`;
const options = { withCredentials: true };
const blank = { name: '', rating: 5, review_text: '', role: '', display_order: 0, is_sample: true, outcome: '' };
const errorText = e => typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Check the fields and try again.';

export const LandingManager = ({ courses }) => {
  const [settings, setSettings] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [editing, setEditing] = useState(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const load = async () => {
    try {
      const [s, r, a] = await Promise.all(['settings', 'reviews', 'analytics'].map(path => axios.get(`${API}/${path}`, options)));
      setSettings(s.data); setReviews(r.data); setAnalytics(a.data); setError('');
    } catch (e) { setError(errorText(e)); }
  };
  useEffect(() => { load(); }, []);
  const saveSettings = async e => {
    e.preventDefault(); setSaving(true);
    try { await axios.put(`${API}/settings`, settings, options); toast.success('Landing settings saved'); }
    catch (e) { toast.error(errorText(e)); } finally { setSaving(false); }
  };
  const saveReview = async e => {
    e.preventDefault(); setSaving(true);
    const { id, ...body } = editing;
    try {
      if (id) await axios.put(`${API}/reviews/${id}`, body, options);
      else await axios.post(`${API}/reviews`, body, options);
      setEditing(null); await load(); toast.success('Review saved');
    } catch (e) { toast.error(errorText(e)); } finally { setSaving(false); }
  };
  const remove = async review => {
    if (!window.confirm(`Delete review by ${review.name}?`)) return;
    try { await axios.delete(`${API}/reviews/${review.id}`, options); await load(); toast.success('Review deleted'); }
    catch (e) { toast.error(errorText(e)); }
  };
  if (!settings) return <div data-testid="landing-admin-loading">{error || 'Loading landing page settings…'}{error && <Button data-testid="landing-admin-retry" onClick={load}>Retry</Button>}</div>;
  return <div className="space-y-8" data-testid="landing-admin-manager">
    <div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-lg font-bold">Data Analytics landing page</h2><p className="text-sm text-slate-500">Reviews, availability, instructor details and first-party analytics.</p></div><a href="/courses/data-analytics" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-orange-700 min-h-12" data-testid="landing-preview-link">Open landing page<ExternalLink size={16} /></a></div>
    <form onSubmit={saveSettings} className="space-y-5" data-testid="landing-settings-form"><div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div><Label htmlFor="landing-course">Linked course (₹1,299)</Label><Select value={settings.course_id} onValueChange={value => setSettings({ ...settings, course_id: value })}><SelectTrigger id="landing-course" data-testid="landing-linked-course" className="h-11 mt-2"><SelectValue placeholder="Select a course" /></SelectTrigger><SelectContent>{courses.map(c => <SelectItem key={c.course_id} value={c.course_id} data-testid={`landing-course-option-${c.course_id}`}>{`${c.title}${!c.published ? ' (draft)' : ''}`}</SelectItem>)}</SelectContent></Select></div>
      {[
        ['seats_filled', 'Seats filled', 'number'], ['seats_total', 'Total seats', 'number'], ['instructor_name', 'Instructor name', 'text'],
        ['instructor_experience', 'Years of experience', 'text'],
        ['support_email', 'Support email', 'email'], ['whatsapp_number', 'WhatsApp number with country code', 'text'], ['instagram_url', 'Instagram profile URL', 'url'], ['linkedin_url', 'LinkedIn profile URL', 'url'],
      ].map(([key, label, type]) => <div key={key}><Label htmlFor={`landing-${key}`}>{label}</Label><Input id={`landing-${key}`} data-testid={`landing-setting-${key.replaceAll('_', '-')}`} type={type} min={key === 'seats_total' ? 1 : 0} max={type === 'number' ? 100000 : undefined} className="mt-2 h-11" value={settings[key]} onChange={e => setSettings({ ...settings, [key]: type === 'number' ? Number(e.target.value) : e.target.value })} /></div>)}
    </div><div><Label htmlFor="landing-instructor-bio">Instructor background</Label><Textarea id="landing-instructor-bio" data-testid="landing-setting-instructor-bio" className="mt-2" value={settings.instructor_bio} maxLength={800} onChange={e => setSettings({ ...settings, instructor_bio: e.target.value })} /></div><p className="text-sm text-amber-800" data-testid="landing-admin-publish-note">The linked course must be published, priced at ₹1,299, and contain your real course content before enrollment opens. Leave unknown social/contact links blank.</p><Button type="submit" disabled={saving} data-testid="landing-save-settings"><Save size={16} className="mr-2" />Save settings</Button></form>
    <section className="border-t pt-6"><div className="flex flex-wrap justify-between items-center gap-3 mb-5"><h3 className="text-lg font-semibold" data-testid="landing-admin-review-count">Landing reviews ({reviews.length})</h3><Button onClick={() => setEditing({ ...blank, display_order: reviews.length })} data-testid="landing-add-review"><Plus size={16} className="mr-2" />Add review</Button></div><p className="text-sm text-slate-500 mb-5">Sample content is labelled publicly and never affects genuine course ratings. Only remove the sample flag after replacing it with an authentic testimonial.</p><div className="grid md:grid-cols-2 gap-4">{reviews.map(r => <article className="border rounded-lg p-4 bg-white min-w-0" key={r.id} data-testid={`admin-review-${r.id}`}><div className="flex justify-between gap-2"><div><strong>{r.name}</strong><span className="text-sm text-amber-700 block">{'★'.repeat(r.rating)} {r.is_sample ? ' · Sample' : ' · Published testimonial'}</span></div><div className="flex"><Button variant="ghost" size="icon" title="Edit review" aria-label={`Edit ${r.name}`} data-testid={`edit-review-${r.id}`} onClick={() => setEditing({ ...r })}><Pencil size={16} /></Button><Button variant="ghost" size="icon" title="Delete review" aria-label={`Delete ${r.name}`} data-testid={`delete-review-${r.id}`} onClick={() => remove(r)}><Trash2 size={16} className="text-red-600" /></Button></div></div><p className="text-sm text-slate-600 my-3 break-words">{r.review_text}</p><small className="text-slate-500">{r.role || 'No role'} · Order {r.display_order}</small></article>)}</div></section>
    <section className="border-t pt-6" data-testid="landing-analytics"><div className="flex gap-4 items-center mb-4"><h3 className="text-lg font-semibold">Conversion analytics · last 30 days</h3><Button variant="outline" size="icon" data-testid="refresh-landing-analytics" title="Refresh analytics" onClick={load}><RefreshCw size={16} /></Button></div><div className="grid md:grid-cols-3 gap-4">{analytics && Object.entries(analytics.by_browser).map(([browser, stats]) => <div key={browser} className="border p-5 rounded-lg" data-testid={`analytics-${browser}`}><h4 className="capitalize font-bold mb-3">{browser === 'browser' ? 'Regular browser' : browser}</h4>{[['page_view', 'Page views'], ['webinar_click', 'Webinar clicks'], ['course_click', 'Course clicks'], ['calculator_interaction', 'Calculator interactions'], ['signup_started', 'Signup starts'], ['signup_completed', 'Verified new signups'], ['purchase_completed', 'Verified purchases']].map(([key, label]) => <p key={key} className="flex justify-between gap-3 text-sm my-2" data-testid={`analytics-${browser}-${key}`}><span>{label}</span><strong>{stats[key]?.events || 0}</strong></p>)}<p className="text-sm border-t pt-3 mt-3" data-testid={`analytics-rate-${browser}`}>Signup completion: <b>{stats.signup_completion_rate}%</b></p></div>)}</div><p className="text-sm text-slate-500 mt-4" data-testid="analytics-attribution-note">{analytics?.note} Browser type is preserved when opening Instagram traffic in an external browser.</p></section>
    <LandingReviewEditor editing={editing} setEditing={setEditing} saving={saving} onSave={saveReview} />
  </div>;
};