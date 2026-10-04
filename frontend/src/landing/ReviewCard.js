import { Flag } from 'lucide-react';

export const ReviewCard = ({ review, index }) => <article className="lp-review-card" data-testid={`review-card-${index}`}>
  <div className="lp-review-card-top"><span className="lp-stars" aria-label={`${review.rating} out of 5 stars`}>{'★'.repeat(review.rating)}{'☆'.repeat(5 - review.rating)}</span>{review.is_sample && <span className="lp-sample-label" data-testid={`review-sample-${index}`}>Sample</span>}</div>
  {!review.is_sample && review.outcome && <p className="lp-review-outcome" data-testid={`review-outcome-${index}`}><Flag size={17} aria-hidden="true" />{review.outcome}</p>}
  <blockquote>{review.review_text}</blockquote>
  <div className="lp-review-author"><span className={`lp-author-initial lp-author-${index % 4}`}>{review.name.split(' ').map(n => n[0]).slice(0, 2).join('')}</span><div><strong>{review.name}</strong>{review.role && <span>{review.role}</span>}</div><span className="lp-quote-mark" aria-hidden="true">”</span></div>
</article>;