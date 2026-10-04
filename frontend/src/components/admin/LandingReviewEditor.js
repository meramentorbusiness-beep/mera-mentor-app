import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';

export const LandingReviewEditor = ({ editing, setEditing, saving, onSave }) => <Dialog open={Boolean(editing)} onOpenChange={open => !open && setEditing(null)}>
  <DialogContent data-testid="landing-review-dialog" className="max-h-[90vh] overflow-y-auto">
    <DialogHeader><DialogTitle>{editing?.id ? 'Edit review' : 'Add review'}</DialogTitle><DialogDescription>Use genuine reviews or keep the sample label enabled.</DialogDescription></DialogHeader>
    {editing && <form onSubmit={onSave} className="space-y-4">
      {[
        ['name', 'Student name', 'text'], ['role', 'Role (optional)', 'text'],
        ['rating', 'Rating (1–5)', 'number'], ['display_order', 'Display order', 'number'],
      ].map(([key, label, type]) => <div key={key}>
        <Label htmlFor={`review-${key}`}>{label}</Label>
        <Input id={`review-${key}`} data-testid={`review-input-${key.replaceAll('_', '-')}`} required={key !== 'role'} type={type}
          min={key === 'rating' ? 1 : 0} max={key === 'rating' ? 5 : type === 'number' ? 10000 : undefined}
          value={editing[key]} onChange={e => setEditing({ ...editing, [key]: type === 'number' ? Number(e.target.value) : e.target.value })} />
      </div>)}
      <div><Label htmlFor="review-text">Review</Label><Textarea id="review-text" data-testid="review-input-text" value={editing.review_text} required minLength={3} maxLength={1000} onChange={e => setEditing({ ...editing, review_text: e.target.value })} /></div>
      <label className="flex gap-3 items-center"><input type="checkbox" data-testid="review-sample-checkbox" checked={editing.is_sample} onChange={e => setEditing({ ...editing, is_sample: e.target.checked, outcome: e.target.checked ? '' : editing.outcome })} />Label as sample content</label>
      <div><Label htmlFor="review-outcome">Concrete outcome (optional)</Label>
        <Input id="review-outcome" data-testid="review-input-outcome" value={editing.outcome || ''} disabled={editing.is_sample} maxLength={80}
          placeholder="e.g. Landed a job or Switched careers" onChange={e => setEditing({ ...editing, outcome: e.target.value })} />
        <p className="text-xs text-slate-500 mt-2" data-testid="review-outcome-guidance">Only add an outcome actually reported by this learner. Outcome tags are never shown on sample reviews.</p>
      </div>
      <Button type="submit" disabled={saving} data-testid="save-landing-review">{saving ? 'Saving…' : 'Save review'}</Button>
    </form>}
  </DialogContent>
</Dialog>;