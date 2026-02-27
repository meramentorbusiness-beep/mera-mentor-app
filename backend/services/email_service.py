# Resend Email Service for Mera Mentor
import os
import resend
from typing import Optional
from datetime import datetime

# Configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "noreply@meramentor.in")
RESEND_SUPPORT_EMAIL = os.environ.get("RESEND_SUPPORT_EMAIL", "support@meramentor.in")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://meramentor.in")

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

def is_email_enabled() -> bool:
    """Check if email service is configured"""
    return bool(RESEND_API_KEY)

def _format_inr(amount: float) -> str:
    """Format amount in INR"""
    return f"₹{amount:,.0f}"

# ========== Email Templates ==========

def _base_template(content: str, title: str) -> str:
    """Base HTML email template with Mera Mentor branding"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #0f172a;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0f172a;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="100%" style="max-width: 600px; background-color: #1e293b; border-radius: 16px; overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 30px 40px; text-align: center; background: linear-gradient(135deg, #4f46e5, #7c3aed);">
                            <h1 style="margin: 0; color: white; font-size: 28px; font-weight: bold;">Mera Mentor</h1>
                            <p style="margin: 5px 0 0; color: rgba(255,255,255,0.8); font-size: 14px;">Seekho. Sikhao. Kamao.</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 40px; background-color: #0f172a; text-align: center; border-top: 1px solid #334155;">
                            <p style="margin: 0 0 10px; color: #94a3b8; font-size: 12px;">
                                Need help? Contact us at <a href="mailto:{RESEND_SUPPORT_EMAIL}" style="color: #818cf8;">{RESEND_SUPPORT_EMAIL}</a>
                            </p>
                            <p style="margin: 0; color: #64748b; font-size: 11px;">
                                © {datetime.now().year} Mera Mentor. All rights reserved.
                            </p>
                            <p style="margin: 10px 0 0; color: #475569; font-size: 10px;">
                                <a href="{FRONTEND_URL}/unsubscribe" style="color: #64748b;">Unsubscribe</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""

# ========== Email Functions ==========

async def send_welcome_email(user_email: str, user_name: str, referral_code: str) -> Optional[str]:
    """Send welcome email after Google OAuth signup"""
    if not is_email_enabled():
        return None
    
    referral_link = f"{FRONTEND_URL}/login?ref={referral_code}"
    
    content = f"""
    <h2 style="margin: 0 0 20px; color: #f1f5f9; font-size: 24px;">Mera Mentor pe Swagat hai! 🎉</h2>
    <p style="margin: 0 0 15px; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
        Namaste <strong style="color: white;">{user_name}</strong>!
    </p>
    <p style="margin: 0 0 25px; color: #94a3b8; font-size: 14px; line-height: 1.6;">
        Aap ab Mera Mentor family ka hissa ho. Ab aap premium courses se seekh sakte ho aur dusro ko refer karke kamaa sakte ho!
    </p>
    
    <!-- Earning Potential Box -->
    <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); border-radius: 12px; padding: 25px; margin: 20px 0;">
        <p style="margin: 0 0 15px; color: white; font-size: 16px; font-weight: bold;">
            💰 Aapka earning potential:
        </p>
        <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 14px; line-height: 1.8;">
            Sirf 5 logo ko refer karo, woh bhi 5-5 karein:<br>
            L1 (5 people) = ₹1,600<br>
            L2 (25 people) = ₹2,400<br>
            L3 (125 people) = ₹6,000<br>
            L4 (625 people) = ₹15,000<br>
            L5 (3125 people) = ₹25,000
        </p>
        <p style="margin: 15px 0 0; color: #fbbf24; font-size: 20px; font-weight: bold;">
            Total: ₹50,000+ 🔥
        </p>
    </div>
    
    <!-- Referral Link -->
    <p style="margin: 25px 0 10px; color: #94a3b8; font-size: 13px;">Your referral link:</p>
    <div style="background: #0f172a; border-radius: 8px; padding: 15px; word-break: break-all;">
        <a href="{referral_link}" style="color: #818cf8; font-size: 14px; text-decoration: none;">{referral_link}</a>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="{FRONTEND_URL}/courses" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 14px;">
            Explore Courses →
        </a>
    </div>
    """
    
    try:
        result = resend.Emails.send({
            "from": f"Mera Mentor <{RESEND_FROM_EMAIL}>",
            "to": [user_email],
            "subject": "Mera Mentor pe Swagat hai! 🎉",
            "html": _base_template(content, "Welcome to Mera Mentor"),
        })
        return result.get("id")
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return None

async def send_purchase_confirmation(
    user_email: str, user_name: str, 
    course_title: str, amount: float, 
    transaction_id: str
) -> Optional[str]:
    """Send purchase confirmation email"""
    if not is_email_enabled():
        return None
    
    content = f"""
    <h2 style="margin: 0 0 20px; color: #f1f5f9; font-size: 24px;">Course Purchase Confirmed! 🎓</h2>
    <p style="margin: 0 0 15px; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
        Hi <strong style="color: white;">{user_name}</strong>,
    </p>
    <p style="margin: 0 0 25px; color: #94a3b8; font-size: 14px; line-height: 1.6;">
        Congratulations! Aapka course purchase successful ho gaya hai.
    </p>
    
    <!-- Order Details -->
    <div style="background: #0f172a; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <table width="100%" style="border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">Course:</td>
                <td style="padding: 10px 0; color: white; font-size: 14px; text-align: right; font-weight: bold;">{course_title}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">Amount Paid:</td>
                <td style="padding: 10px 0; color: #22c55e; font-size: 16px; text-align: right; font-weight: bold;">{_format_inr(amount)}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">Transaction ID:</td>
                <td style="padding: 10px 0; color: #818cf8; font-size: 12px; text-align: right; font-family: monospace;">{transaction_id}</td>
            </tr>
        </table>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 14px;">
            Start Learning →
        </a>
    </div>
    """
    
    try:
        result = resend.Emails.send({
            "from": f"Mera Mentor <{RESEND_FROM_EMAIL}>",
            "to": [user_email],
            "subject": "Course Purchase Confirmed! 🎓",
            "html": _base_template(content, "Purchase Confirmed"),
        })
        return result.get("id")
    except Exception as e:
        print(f"Error sending purchase email: {e}")
        return None

async def send_commission_earned(
    user_email: str, user_name: str,
    amount: float, from_user_name: str,
    level: int, total_earned: float
) -> Optional[str]:
    """Send commission earned notification"""
    if not is_email_enabled():
        return None
    
    content = f"""
    <h2 style="margin: 0 0 20px; color: #f1f5f9; font-size: 24px;">🎉 {_format_inr(amount)} kamaya aapne!</h2>
    <p style="margin: 0 0 15px; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
        Hi <strong style="color: white;">{user_name}</strong>,
    </p>
    <p style="margin: 0 0 25px; color: #94a3b8; font-size: 14px; line-height: 1.6;">
        Badhai ho! Aapne abhi commission kamaya hai!
    </p>
    
    <!-- Commission Details -->
    <div style="background: linear-gradient(135deg, #059669, #10b981); border-radius: 12px; padding: 25px; margin: 20px 0; text-align: center;">
        <p style="margin: 0; color: rgba(255,255,255,0.8); font-size: 14px;">Commission Earned</p>
        <p style="margin: 10px 0; color: white; font-size: 36px; font-weight: bold;">{_format_inr(amount)}</p>
        <p style="margin: 0; color: rgba(255,255,255,0.7); font-size: 12px;">
            Level {level} referral from {from_user_name}
        </p>
    </div>
    
    <div style="background: #0f172a; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <table width="100%" style="border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">Total Earnings:</td>
                <td style="padding: 10px 0; color: #22c55e; font-size: 18px; text-align: right; font-weight: bold;">{_format_inr(total_earned)}</td>
            </tr>
        </table>
    </div>
    
    <p style="margin: 25px 0 0; color: #94a3b8; font-size: 13px; text-align: center;">
        Commission 7 din baad withdrawable ho jayega.
    </p>
    
    <div style="text-align: center; margin-top: 20px;">
        <a href="{FRONTEND_URL}/wallet" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 14px;">
            View Wallet →
        </a>
    </div>
    """
    
    try:
        result = resend.Emails.send({
            "from": f"Mera Mentor <{RESEND_FROM_EMAIL}>",
            "to": [user_email],
            "subject": f"🎉 {_format_inr(amount)} kamaya aapne!",
            "html": _base_template(content, "Commission Earned"),
        })
        return result.get("id")
    except Exception as e:
        print(f"Error sending commission email: {e}")
        return None

async def send_payout_processed(
    user_email: str, user_name: str,
    amount: float, utr_number: str
) -> Optional[str]:
    """Send payout processed confirmation"""
    if not is_email_enabled():
        return None
    
    content = f"""
    <h2 style="margin: 0 0 20px; color: #f1f5f9; font-size: 24px;">💰 {_format_inr(amount)} aapke account mein!</h2>
    <p style="margin: 0 0 15px; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
        Hi <strong style="color: white;">{user_name}</strong>,
    </p>
    <p style="margin: 0 0 25px; color: #94a3b8; font-size: 14px; line-height: 1.6;">
        Aapka payout successfully process ho gaya hai!
    </p>
    
    <!-- Payout Details -->
    <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); border-radius: 12px; padding: 25px; margin: 20px 0; text-align: center;">
        <p style="margin: 0; color: rgba(255,255,255,0.8); font-size: 14px;">Amount Transferred</p>
        <p style="margin: 10px 0; color: white; font-size: 36px; font-weight: bold;">{_format_inr(amount)}</p>
    </div>
    
    <div style="background: #0f172a; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <table width="100%" style="border-collapse: collapse;">
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">UTR Number:</td>
                <td style="padding: 10px 0; color: #818cf8; font-size: 14px; text-align: right; font-family: monospace;">{utr_number}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; color: #94a3b8; font-size: 13px;">Date:</td>
                <td style="padding: 10px 0; color: white; font-size: 14px; text-align: right;">{datetime.now().strftime("%d %b %Y")}</td>
            </tr>
        </table>
    </div>
    
    <p style="margin: 25px 0 0; color: #94a3b8; font-size: 13px; text-align: center;">
        Amount aapke registered bank account mein credit ho gaya hai.
    </p>
    """
    
    try:
        result = resend.Emails.send({
            "from": f"Mera Mentor <{RESEND_FROM_EMAIL}>",
            "to": [user_email],
            "subject": f"💰 {_format_inr(amount)} aapke account mein!",
            "html": _base_template(content, "Payout Processed"),
        })
        return result.get("id")
    except Exception as e:
        print(f"Error sending payout email: {e}")
        return None

async def send_referral_nudge(
    user_email: str, user_name: str,
    referrer_name: str, top_courses: list
) -> Optional[str]:
    """Send referral nudge to inactive users"""
    if not is_email_enabled():
        return None
    
    courses_html = ""
    for course in top_courses[:3]:
        courses_html += f"""
        <div style="background: #0f172a; border-radius: 8px; padding: 15px; margin-bottom: 10px; display: flex; align-items: center;">
            <div style="flex: 1;">
                <p style="margin: 0; color: white; font-size: 14px; font-weight: bold;">{course['title']}</p>
                <p style="margin: 5px 0 0; color: #94a3b8; font-size: 12px;">{course['category']}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0; color: #22c55e; font-size: 16px; font-weight: bold;">{_format_inr(course['price'])}</p>
            </div>
        </div>
        """
    
    content = f"""
    <h2 style="margin: 0 0 20px; color: #f1f5f9; font-size: 24px;">{referrer_name} aapka intezaar kar rahe hain! 👋</h2>
    <p style="margin: 0 0 15px; color: #cbd5e1; font-size: 16px; line-height: 1.6;">
        Hi <strong style="color: white;">{user_name}</strong>,
    </p>
    <p style="margin: 0 0 25px; color: #94a3b8; font-size: 14px; line-height: 1.6;">
        Aapne abhi tak koi course nahi liya. Aap miss kar rahe ho amazing learning opportunities!
    </p>
    
    <p style="margin: 0 0 15px; color: #f1f5f9; font-size: 16px; font-weight: bold;">Top Courses:</p>
    {courses_html}
    
    <div style="text-align: center; margin-top: 30px;">
        <a href="{FRONTEND_URL}/courses" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 14px 32px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 14px;">
            Browse Courses →
        </a>
    </div>
    """
    
    try:
        result = resend.Emails.send({
            "from": f"Mera Mentor <{RESEND_FROM_EMAIL}>",
            "to": [user_email],
            "subject": f"{referrer_name} aapka intezaar kar rahe hain!",
            "html": _base_template(content, "Don't Miss Out"),
        })
        return result.get("id")
    except Exception as e:
        print(f"Error sending nudge email: {e}")
        return None
