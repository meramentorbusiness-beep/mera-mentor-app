import { useState } from 'react';
import { ArrowUpRight, Check, TrendingUp, Users } from 'lucide-react';
import { money } from './content';
import { track } from './client';

export const SalaryCalculator = () => {
  const [salary, setSalary] = useState(20000);
  const target = 45000;
  const gain = target - salary;
  const days = (1299 / (target / 30)).toFixed(1);
  return <section className="lp-section lp-career" id="career" aria-labelledby="career-heading">
    <div className="lp-wrap">
      <div className="lp-section-top"><span className="lp-eyebrow">A SMALL INVESTMENT. A BIGGER TOMORROW.</span><span className="lp-section-number">02 / THE POSSIBILITIES</span></div>
      <h2 className="lp-heading" id="career-heading">Course Investment.<br /><span>Career Return.</span></h2>
      <div className="lp-roi-grid">
        <div>
          <div className="lp-roi-numbers" data-testid="career-roi-comparison"><div><span>COURSE FEE</span><strong>₹1,299</strong><p>One-time investment</p></div><ArrowUpRight size={40} /><div><span>ANALYST SALARY RANGE*</span><strong className="lp-green">₹4–8 LPA</strong><p>Illustrative annual salary</p></div></div>
          <p className="lp-roi-note" data-testid="roi-ratio">300–600× salary-to-fee ratio in Year 1*</p>
          <div className="lp-before-after"><div><h3>Before course</h3><p>No data skills</p><p>₹15–20k/month</p><p>No job security</p></div><div><h3><Check size={18} /> A possible after</h3><p>Data analyst skills</p><p>₹35–70k/month*</p><p>High-demand skill set</p></div></div>
        </div>
        <div className="lp-calculator lp-salary-tool" data-testid="salary-calculator">
          <div className="lp-tool-title"><TrendingUp size={22} /><h3>Aapka next chapter, in numbers.</h3></div>
          <label htmlFor="salary-slider">Aapki current monthly salary</label><output htmlFor="salary-slider" className="lp-slider-value" data-testid="current-salary">₹{money(salary)}</output>
          <input type="range" id="salary-slider" min="0" max="80000" step="1000" value={salary} onChange={e => setSalary(Number(e.target.value))} onPointerUp={() => track('calculator_interaction', 'salary', salary)} onKeyUp={() => track('calculator_interaction', 'salary', salary)} data-testid="salary-slider" />
          <div className="lp-range-labels"><span>₹0</span><span>₹80,000</span></div>
          <div className="lp-salary-result" aria-live="polite"><span>At an illustrative ₹45,000/month</span><strong key={gain} className="lp-count" data-testid="salary-gain">{gain > 0 ? `+₹${money(gain)}` : gain === 0 ? '₹0 difference' : `₹${money(Math.abs(gain))} lower`}<small>{gain > 0 ? ' more / month' : ''}</small></strong><p data-testid="salary-payback">{gain > 0 ? `Course pays for itself in ${days} days of new salary.` : 'Is example mein salary increase nahi hai. Compare skills and opportunities, not just pay.'}</p></div>
        </div>
      </div>
      <p className="lp-disclaimer" data-testid="salary-disclaimer">*Illustrative scenarios, not guaranteed outcomes or verified salary averages. Salary-to-fee ratio is not investment ROI. Actual salary depends on experience, location, effort and the job market.</p>
    </div>
  </section>;
};

const levels = [440, 132, 66, 33, 11];
export const ReferralCalculator = () => {
  const [count, setCount] = useState(5);
  const [chain, setChain] = useState(false);
  const direct = count * levels[0];
  const total = levels.reduce((sum, rate, i) => sum + Math.pow(count, i + 1) * rate, 0);
  return <section className="lp-section lp-referral" id="referrals" aria-labelledby="referral-heading"><div className="lp-wrap lp-referral-layout">
    <div className="lp-referral-copy"><span className="lp-eyebrow">SEEKHO. SHARE KARO. KAMAO.</span><h2 id="referral-heading" className="lp-heading">Achhi cheezein<br />doston ke saath<br /><span>share karte hain.</span></h2><p>Course Lo, Dosto Ko Batao, Kamao!<br />Aap grow karo. Apni community ko bhi grow karao.</p><div className="lp-free-callout"><Users size={28} /><p>Sirf <strong>3 dost</strong> join karein,<br />toh course ki cost recover ho sakti hai.</p></div><span className="lp-equation">3 × ₹440 = ₹1,320 &gt; ₹1,299</span></div>
    <div className="lp-calculator lp-referral-tool" data-testid="referral-calculator"><div className="lp-tool-title"><span>YOUR REFERRAL POTENTIAL</span><span aria-hidden="true">↗</span></div>
      <div className="lp-segmented" role="group" aria-label="Referral calculation mode">{['Simple', 'Chain Effect'].map((label, i) => <button key={label} className={chain === Boolean(i) ? 'active' : ''} type="button" aria-pressed={chain === Boolean(i)} data-testid={`referral-mode-${i ? 'chain' : 'simple'}`} onClick={() => { setChain(Boolean(i)); track('calculator_interaction', i ? 'chain' : 'simple', count); }}>{label}</button>)}</div>
      <div className="lp-slider-heading"><label htmlFor="referral-slider">Kitne dost refer karoge?</label><output htmlFor="referral-slider" data-testid="referral-count">{count} dost</output></div>
      <input id="referral-slider" data-testid="referral-slider" type="range" min="1" max="20" value={count} onChange={e => setCount(Number(e.target.value))} onPointerUp={() => track('calculator_interaction', 'referral', count)} onKeyUp={() => track('calculator_interaction', 'referral', count)} /><div className="lp-range-labels"><span>1 dost</span><span>20 dost</span></div>
      <div className="lp-referral-result" aria-live="polite"><span>{chain ? '5-level chain ki illustrative kamai' : `Agar aap ${count} dost refer karo`}</span><strong key={`${count}-${chain}`} className="lp-count" data-testid="referral-earnings">₹{money(chain ? total : direct)}<span aria-hidden="true">{chain ? ' 🔥' : ' 💰'}</span></strong><span>{chain ? `Har person ${count} paying friends refer kare, har level par.` : 'Aapki potential direct kamai'}</span></div>
      <div className="lp-commission-levels">{levels.map((rate, i) => <div key={rate}><span>L{i + 1} · {[40, 12, 6, 3, 1][i]}%</span><strong>≈ ₹{rate}</strong></div>)}</div>
      {chain && <div className="lp-chain-breakdown" data-testid="chain-breakdown">{levels.map((rate, i) => <p key={rate}>L{i + 1}: {money(Math.pow(count, i + 1))} purchases <strong>₹{money(Math.pow(count, i + 1) * rate)}</strong></p>)}</div>}
      <p className="lp-disclaimer" data-testid="referral-disclaimer">Estimates use rounded commissions on ₹1,101 before GST. Every referral must purchase; earnings are not guaranteed. Actual payouts use exact rates, applicable deductions and program terms.</p>
    </div>
  </div></section>;
};