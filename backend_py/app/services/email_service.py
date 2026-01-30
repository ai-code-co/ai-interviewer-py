## backend_py/app/services/email_service.py
from __future__ import annotations
import requests
from ..config import get_settings

def _mailgun_sending_disabled() -> bool:
    """
    Allow skipping Mailgun sends in development/testing.
    """
    import os
    val = os.getenv("MAILGUN_DISABLE_SEND") or os.getenv("MAILGUN_TEST_MODE")
    return str(val).lower() in {"1", "true", "yes", "on"}

def should_soft_fail_mailgun(message: str | None) -> bool:
    if _mailgun_sending_disabled(): return True
    if not message: return False
    lower = message.lower()
    return "authorized recipients" in lower or "sandbox" in lower

def _get_email_config() -> dict:
    settings = get_settings()
    if not settings.mailgun_api_key or not settings.mailgun_domain:
        raise RuntimeError("MAILGUN_API_KEY or MAILGUN_DOMAIN not configured")
    return {
        "api_key": settings.mailgun_api_key,
        "domain": settings.mailgun_domain,
        "from_address": settings.mail_from_address,
        "from_name": settings.mail_from_name,
    }

def _send_mailgun_message(to: str, subject: str, text: str, html: str) -> None:
    config = _get_email_config()
    url = f"https://api.mailgun.net/v3/{config['domain']}/messages"
    auth = ("api", config["api_key"])
    data = {
        "from": f"{config['from_name']} <{config['from_address']}>",
        "to": [to],
        "subject": subject,
        "text": text,
        "html": html,
    }
    resp = requests.post(url, auth=auth, data=data, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"Failed to send email via Mailgun: {resp.status_code} {resp.text}")

# --- 1. INVITE CANDIDATE EMAIL ---
def send_invite_email(email: str, invite_url: str) -> None:
    if _mailgun_sending_disabled():
        print(f"[mailgun] Invite email skipped. URL: {invite_url}")
        return

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #333;">You've been invited to apply</h2>
      <p style="color: #666; line-height: 1.6;">
        You have been invited to apply for a position. This link expires in 48 hours.
      </p>
      
      <div style="margin: 30px 0;">
        <a 
          href="{invite_url}" 
          style="display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;"
        >
          Apply Now
        </a>
      </div>
      
      <p style="color: #999; font-size: 14px; margin-top: 30px;">
        Or copy and paste this link into your browser:<br/>
        <a href="{invite_url}" style="color: #007bff;">{invite_url}</a>
      </p>
    </div>
    """
    
    text = f"You've been invited to apply.\n\nLink: {invite_url}"
    _send_mailgun_message(email, "Invitation to Apply", text, html)


# --- 2. APPROVAL / INTERVIEW EMAIL ---
def send_approval_email(email: str, job_title: str, custom_message: str, interview_link: str = "") -> None:
    if _mailgun_sending_disabled():
        print(f"[mailgun] Approval email skipped. Link: {interview_link}")
        return

    action_section = ""
    if interview_link:
        action_section = f"""
        <div style="margin: 30px 0; padding: 20px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
            <p style="font-weight: bold; margin-top: 0;">Next Step: AI Interview</p>
            <div style="margin: 20px 0;">
                <a href="{interview_link}" style="background-color: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                    Start AI Interview
                </a>
            </div>
            <p style="font-size: 13px; color: #666; margin-bottom: 0;">
                If the button doesn't work, copy this link:<br>
                <a href="{interview_link}" style="color: #2563eb;">{interview_link}</a>
            </p>
        </div>
        """

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #28a745; margin-top: 0;">Congratulations! 🎉</h2>
      <p style="color: #333; font-size: 16px;">
        We are pleased to inform you that your application for <strong>{job_title}</strong> has been approved!
      </p>
      
      {f'<div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">{custom_message}</div>' if custom_message else ''}
      
      {action_section}
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        Best regards,<br/>
        The Hiring Team
      </p>
    </div>
    """
    
    text = f"Congratulations! Your application for {job_title} has been approved.\n\n{custom_message}\n\nStart Interview: {interview_link}"
    _send_mailgun_message(email, f"Application Approved - {job_title}", text, html)


# --- 3. REJECTION EMAIL ---
def send_rejection_email(email: str, job_title: str, custom_message: str) -> None:
    if _mailgun_sending_disabled():
        print("[mailgun] Rejection email skipped")
        return

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #333;">Application Update</h2>
      <p style="color: #333;">Regarding your application for <strong>{job_title}</strong>.</p>
      
      <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0;">
        {custom_message or "Thank you for your interest. Unfortunately, we have decided to move forward with other candidates."}
      </div>
      
      <p style="color: #666; font-size: 14px;">
        We wish you the best in your job search.
      </p>
    </div>
    """
    text = f"Update regarding {job_title}.\n\n{custom_message}"
    _send_mailgun_message(email, f"Application Update - {job_title}", text, html)

def send_offer_email(email: str, job_title: str, custom_message: str) -> None:
    if _mailgun_sending_disabled():
        print(f"[mailgun] Offer email skipped.")
        return

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #28a745; margin-top: 0;">Job Offer: {job_title} 🎉</h2>
      <p style="color: #333; font-size: 16px;">
        We are delighted to offer you the position of <strong>{job_title}</strong>!
      </p>
      
      <div style="background-color: #f0fdf4; padding: 20px; border: 1px solid #bbf7d0; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 0; font-style: italic;">{custom_message}</p>
      </div>
      
      <p style="color: #666; font-size: 14px; margin-top: 30px;">
        Our team will be in touch shortly with the official offer letter and next steps.
      </p>
      <p style="color: #666; font-size: 14px;">
        Best regards,<br/>
        The Hiring Team
      </p>
    </div>
    """
    
    text = f"Job Offer: {job_title}\n\n{custom_message}\n\nOur team will contact you shortly."
    _send_mailgun_message(email, f"Job Offer - {job_title}", text, html)