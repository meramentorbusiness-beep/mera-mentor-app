"""Idempotent landing content, kept separate from genuine learner reviews."""
from sqlalchemy import select, text
from models.models import Course, LandingPage, Review

SLUG = "data-analytics"
DEFAULTS = {
    "course_id": "course_data_analytics", "seats_filled": 0, "seats_total": 50,
    "instructor_name": "Himanshu", "instructor_experience": "4+",
    "instructor_bio": "Industry mein real data projects pe kaam, aur 200+ interns ko mentor kiya. Complex concepts ko simple banana aur practical projects se sikhana — yahi approach hai.",
    "support_email": "Nikhilparwani205@gmail.com", "whatsapp_number": "",
    "instagram_url": "", "linkedin_url": "https://linkedin.com/in/himanshu--bhardwaj/",
    "student_count": "500+", "average_rating": "4.8",
}

SAMPLES = [
    ("Aarav Sharma", "SQL pehle scary lagta tha. Everyday examples se joins finally samajh aaye!", "Fresher"),
    ("Priya Verma", "Best ₹1,299 investment! Excel shortcuts ab mere daily work ka part hain.", "Working professional"),
    ("Rohan Mehta", "Coding background bilkul nahi tha. Zero se start kiya, aur ab khud dashboards bana leta hoon.", "B.Com graduate"),
    ("Sneha Patel", "Real datasets pe projects karna sabse useful tha. Portfolio mein dikhane ke liye actual work hai.", "Aspiring data analyst"),
    ("Aditya Singh", "ChatGPT se SQL debug karna seekha. Jo kaam hours leta tha, ab minutes mein ho jaata hai.", "Student"),
    ("Ananya Gupta", "Resume session ne kaafi clarity di. Apne projects ko interview mein confidently explain kar paati hoon.", "Graduate"),
    ("Karan Joshi", "Office ke baad apni pace par seekh sakta hoon. Lifetime access mere liye sabse bada plus hai.", "Working professional"),
    ("Ishita Rao", "Power BI ko itna simply explain kiya! Pehla dashboard banaya toh honestly proud feel hua.", "Engineering student"),
    ("Rahul Yadav", "Doubts ka response fast tha. Beginner questions poochhne mein bhi hesitation nahi hui.", "Career switcher"),
    ("Neha Kapoor", "Sirf theory nahi, har topic ke saath practice. Data cleaning ka importance ab samajh aaya.", "Student"),
    ("Vikram Desai", "Interview prep genuinely practical thi. Pehla analytics interview crack karne ka confidence mila.", "Aspiring analyst"),
    ("Simran Kaur", "Hindi-English explanation natural hai. Technical terms ko samajhne ke liye baar-baar Google nahi karna pada.", "BBA graduate"),
    ("Mohit Kumar", "SQL practice aur project work ke baad 2 months mein placement mili. Consistency ne difference banaya.", "Junior data analyst"),
    ("Pooja Nair", "Excel aata tha, lekin analysis nahi. Ab numbers ke peeche ki story samajh paati hoon.", "Operations professional"),
    ("Arjun Reddy", "AI tools wala module favourite hai. Prompting ke saath output verify karna bhi seekha.", "Engineering graduate"),
    ("Kavya Shah", "Itni affordable price par structured roadmap mil gaya. Ab random tutorials mein time waste nahi hota.", "Student"),
    ("Manish Tiwari", "Non-tech se switch karna intimidating tha. Step-by-step approach ne journey manageable bana di.", "Career switcher"),
    ("Divya Menon", "Live doubt sessions helpful the. Apne dashboard par feedback milna really valuable tha.", "Aspiring analyst"),
    ("Sahil Khan", "Resume mein projects kaise present karein, yeh seekha. Interview answers ab much more specific hain.", "Fresher"),
    ("Ritika Jain", "Clean dashboards aur clear storytelling dono seekhe. Ab data dekh kar questions poochhna aata hai.", "Business graduate"),
]


async def initialize_landing(db):
    # create_all doesn't migrate existing SQL tables. These additions are repeatable.
    for definition in ["name VARCHAR(100)", "role VARCHAR(160)",
                       "display_order INTEGER DEFAULT 0", "is_landing BOOLEAN DEFAULT FALSE",
                       "is_sample BOOLEAN DEFAULT FALSE"]:
        await db.execute(text(f"ALTER TABLE reviews ADD COLUMN IF NOT EXISTS {definition}"))
    await db.execute(text("ALTER TABLE reviews ALTER COLUMN user_id DROP NOT NULL"))
    await db.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS landing_visitor_id VARCHAR(80)"))
    await db.execute(text("ALTER TABLE purchases ADD COLUMN IF NOT EXISTS landing_browser_type VARCHAR(20)"))
    page = await db.get(LandingPage, SLUG)
    if not page:
        course = (await db.execute(select(Course).where(Course.course_id == DEFAULTS["course_id"]))).scalar_one_or_none()
        if not course:
            # Never sell an empty placeholder course. An admin must attach/publish real content.
            course = Course(course_id=DEFAULTS["course_id"], title="Data Analytics Career Course",
                            description="Excel, SQL, Power BI / Tableau, AI tools aur interview preparation.",
                            price=1299, category="Data Science", published=False)
            db.add(course)
            await db.flush()
        db.add(LandingPage(slug=SLUG, settings=dict(DEFAULTS)))
        for i, (name, review, role) in enumerate(SAMPLES):
            db.add(Review(course_id=course.id, name=name, rating=5, text=review,
                          role=role, display_order=i, is_landing=True, is_sample=True))
    await db.commit()