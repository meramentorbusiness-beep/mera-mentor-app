import { ArrowRight, BookOpenCheck, MessagesSquare, Infinity } from 'lucide-react';
import { WebinarButton } from './Sections';
import { track } from './client';

const commitments = [
  { Icon: BookOpenCheck, title: 'Practical learning', text: 'Excel, SQL, dashboards aur AI tools — guided exercises aur projects ke saath.' },
  { Icon: MessagesSquare, title: 'Doubts ke liye support', text: 'Included live webinar sessions mein questions poochho. Resume aur interview prep bhi course ka part hai.' },
  { Icon: Infinity, title: 'Lifetime course access', text: 'Ek baar enroll karo, phir apni pace par seekho aur zaroorat padne par revise karo.' },
];

export const LearningPromise = ({ webinarUrl }) => <section className="lp-section lp-learning-promise" aria-labelledby="learning-promise-title" data-testid="learning-promise-section">
  <div className="lp-wrap">
    <span className="lp-eyebrow">CLEAR EXPECTATIONS. FROM DAY ONE.</span>
    <div className="lp-promise-intro">
      <h2 className="lp-heading" id="learning-promise-title">Skills par focus.<br /><span>Job ki guarantee nahi.</span></h2>
      <div><p data-testid="no-job-guarantee">Koi bhi course job milne ka pakka vaada nahi kar sakta. Hiring aapki practice, portfolio, interviews aur market par depend karti hai — sirf certificate par nahi.</p><p data-testid="learning-timeline-disclaimer">2 months ek learning goal hai, placement deadline nahi. Aapka progress aapke starting point, time aur practice par depend karega.</p></div>
    </div>
    <h3 className="lp-commitments-title">Hum kis cheez ka commitment dete hain?</h3>
    <div className="lp-commitments">{commitments.map(({ Icon, title, text }, i) => <div key={title} data-testid={`learning-commitment-${i}`}><Icon size={25} /><h3>{title}</h3><p>{text}</p></div>)}</div>
    <div className="lp-promise-actions"><WebinarButton source="promise" url={webinarUrl}>Pehle Free Webinar Join Karo</WebinarButton><a href="#pricing" className="lp-button lp-button-outline" data-testid="course-promise" onClick={() => track('course_click', 'promise')}>Course Details — ₹1,299<ArrowRight size={19} /></a></div>
  </div>
</section>;