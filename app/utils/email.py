import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email(to: str, subject: str, html_body: str) -> None:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = to

        part = MIMEText(html_body, "html")
        msg.attach(part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to, msg.as_string())

        logger.info("Email sent to %s | Subject: %s", to, subject)

    except Exception as e:
        logger.error(
            "Failed to send email to %s | Subject: %s | Error: %s",
            to, subject, str(e)
        )




def send_staff_invitation(
    to: str,
    full_name: str,
    organization_name: str,
    temp_password: str,
) -> None:
    subject = f"Welcome to {organization_name} — Your Account Details"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1E3A5F;">Welcome, {full_name}!</h2>
        <p>Your account has been created on <strong>{organization_name}'s</strong>
        CommissionTrack portal.</p>

        <div style="background: #EBF4F8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Email:</strong> {to}</p>
            <p style="margin: 8px 0 0;"><strong>Temporary Password:</strong>
            <span style="font-family: monospace; font-size: 16px;">{temp_password}</span></p>
        </div>

        <p style="color: #e74c3c;"><strong>Please change your password
        after your first login.</strong></p>

        <p style="color: #777; font-size: 12px;">
        If you did not expect this email, please contact your administrator.
        </p>
    </div>
    """
    _send_email(to, subject, html)


def send_commission_approved(
    to: str,
    full_name: str,
    amount: float,
    period: str,
) -> None:
    subject = f"Your Commission for {period} Has Been Approved"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1E3A5F;">Commission Approved</h2>
        <p>Hi {full_name},</p>
        <p>Great news! Your commission for <strong>{period}</strong>
        has been approved.</p>

        <div style="background: #EBF4F8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; font-size: 24px;">
            <strong>Amount: ₦{amount:,.2f}</strong></p>
            <p style="margin: 8px 0 0; color: #27AE60;">Status: Approved</p>
        </div>

        <p>Your commission will be processed for payment shortly.</p>
    </div>
    """
    _send_email(to, subject, html)


def send_commission_paid(
    to: str,
    full_name: str,
    amount: float,
    period: str,
) -> None:
    subject = f"Your Commission for {period} Has Been Paid"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1E3A5F;">Commission Paid</h2>
        <p>Hi {full_name},</p>
        <p>Your commission for <strong>{period}</strong> has been paid.</p>

        <div style="background: #EBF4F8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; font-size: 24px;">
            <strong>Amount: ₦{amount:,.2f}</strong></p>
            <p style="margin: 8px 0 0; color: #27AE60;">Status: Paid ✓</p>
        </div>

        <p>Thank you for your hard work!</p>
    </div>
    """
    _send_email(to, subject, html)


def send_commission_disputed(
    to: str,
    full_name: str,
    amount: float,
    period: str,
    notes: str = None,
) -> None:
    subject = f"Your Commission for {period} Has Been Disputed"
    notes_section = f"""
        <div style="background: #FFF3CD; padding: 12px;
        border-radius: 4px; margin-top: 12px;">
            <strong>Note from admin:</strong> {notes}
        </div>
    """ if notes else ""

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #C0392B;">Commission Disputed</h2>
        <p>Hi {full_name},</p>
        <p>Your commission for <strong>{period}</strong> has been flagged
        for review.</p>

        <div style="background: #FDECEA; padding: 20px;
        border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; font-size: 24px;">
            <strong>Amount: ₦{amount:,.2f}</strong></p>
            <p style="margin: 8px 0 0; color: #C0392B;">Status: Disputed</p>
            {notes_section}
        </div>

        <p>Please contact your administrator for more information.</p>
    </div>
    """
    _send_email(to, subject, html)


def send_admin_commission_disputed(
    to: str,
    admin_name: str,
    staff_name: str,
    amount: float,
    period: str,
) -> None:
    subject = f"Commission Dispute Raised — {staff_name} ({period})"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1E3A5F;">Commission Dispute Raised</h2>
        <p>Hi {admin_name},</p>
        <p>A commission has been marked as disputed and requires your attention.</p>

        <div style="background: #FDECEA; padding: 20px;
        border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Staff Member:</strong> {staff_name}</p>
            <p style="margin: 8px 0 0;"><strong>Period:</strong> {period}</p>
            <p style="margin: 8px 0 0;"><strong>Amount:</strong>
            ₦{amount:,.2f}</p>
        </div>

        <p>Please log in to review and resolve this dispute.</p>
    </div>
    """
    _send_email(to, subject, html)