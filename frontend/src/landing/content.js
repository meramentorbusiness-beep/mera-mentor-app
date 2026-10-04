export const COURSE_PRICE = 1299;
export const money = value => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(value);
export const stack = [
  { icon: '📊', tag: 'The Foundation', title: 'Advanced Excel & Data Cleaning', detail: '(Jahan 80% kaam hota hai)', color: 'green' },
  { icon: '🗄️', tag: 'The Backbone', title: 'SQL', detail: 'Databases se baat karna aur data extract karna seekho', color: 'blue' },
  { icon: '📈', tag: 'The Story', title: 'Power BI / Tableau', detail: 'Dashboards banao jo stakeholders samajh sakein', color: 'yellow' },
  { icon: '🤖', tag: 'The AI Advantage', title: 'ChatGPT & AI tools', detail: 'Repetitive analysis automate karna aur AI-generated answers verify karna seekho', color: 'orange' },
  { icon: '💼', tag: 'The Job Hunt', title: 'Resume hacks aur interview prep', detail: 'Specially freshers ke liye', color: 'pink' },
];
export const curriculum = [
  { title: 'Data analytics ki foundation', topics: ['Analyst ka role aur analytical thinking', 'Data types, business questions aur real-world use cases'], unlocked: true },
  { title: 'Advanced Excel & data cleaning', topics: ['XLOOKUP, pivot tables aur spreadsheet analysis', 'Messy datasets clean karna aur reporting workflows'], unlocked: true },
  { title: 'SQL: data se answers tak', topics: ['SELECT, filtering, grouping aur joins', 'Subqueries, window functions aur practice datasets'] },
  { title: 'Power BI / Tableau dashboards', topics: ['Data modelling aur visual storytelling', 'Business KPIs aur interactive dashboard project'] },
  { title: 'AI tools for smarter analysis', topics: ['ChatGPT for SQL, Excel formulas aur debugging', 'AI-generated answers validate karna aur responsible workflows'] },
  { title: 'Portfolio, resume & interview prep', topics: ['End-to-end capstone project', 'Resume review, interview questions aur project presentation'] },
];
export const faq = [
  ['Kya refund milega agar course pasand nahi aaya?', 'Nahi, hum no-refund policy follow karte hain. Isliye demo content dekh kar hi decision lein.'],
  ['Course access kitne time tak milega?', 'Lifetime access — ek baar kharido, jab chaho revise karo, koi expiry nahi hai.'],
  ['Kya certificate milega course complete karne par?', 'Haan, Data Analyst Certificate milega jo aap LinkedIn aur resume mein add kar sakte hain.'],
  ['Kya live classes bhi hongi ya sirf recorded videos?', 'Live webinar sessions included hain jahan aap directly doubts clear kar sakte hain, saath mein recorded content bhi milega.'],
  ['Course kaun padha raha hai?', '4+ years ka experienced data expert jo real industry projects pe kaam kar chuka hai, na ki sirf theory teacher.'],
  ['Kya mujhe coding background chahiye is course ke liye?', 'Nahi, yeh course beginners ke liye design kiya gaya hai. Excel se shuru karke SQL, Power BI/Tableau, aur AI tools tak sab step by step sikhaya jaayega.'],
  ['Referral se kitna kama sakte hain?', 'Har referral par commission milta hai — upar calculator use karke apni potential earning dekhein.'],
  ['Job placement ki guarantee hai?', 'Hum job-ready skills, resume hacks, aur interview prep dete hain, lekin placement ki direct guarantee nahi de sakte — yeh aapki mehnat aur market pe depend karta hai.'],
];
export const inclusions = ['Lifetime access to course content', 'Live webinar sessions', 'Data Analyst Certificate on completion', 'Taught by a 4+ years experienced data expert', 'AI tools training included', 'Resume + interview prep'];