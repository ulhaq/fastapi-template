import logging
from email.headerregistry import Address
from email.message import EmailMessage
from smtplib import SMTP

from src.core.config import settings
from src.core.template import templates

log = logging.getLogger(__name__)


def send_email(
    *,
    address: str,
    user_name: str,
    subject: str = "",
    email_template: str,
    data: dict | None = None,
) -> None:
    if data is None:
        data = {}
    data = {
        "app_name": settings.app_name,
        "info_email": settings.email_from_address,
        "user_name": user_name,
    } | data

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = Address(
        settings.email_from_name, addr_spec=settings.email_from_address
    )
    msg["To"] = Address(user_name, addr_spec=address)

    template_html = templates.get_template(f"emails/{email_template}.html").render(
        **data
    )

    msg.set_content(
        "This is an HTML email. Please view it in an HTML-compatible client."
    )
    msg.add_alternative(template_html, subtype="html")

    with SMTP(settings.email_host, settings.email_port) as smtp:
        if settings.email_tls:
            smtp.ehlo()
            if smtp.has_extn("STARTTLS"):
                smtp.starttls()
                smtp.ehlo()
        if settings.email_user and settings.email_password:
            smtp.login(settings.email_user, settings.email_password)
        smtp.send_message(msg)

    log.info("Email sent. [template=%s, ctx=%s]", email_template, data)
