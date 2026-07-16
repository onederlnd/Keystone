# app/core/notifications.py

import aiosmtplib
from jinja2 import Environment, FileSystemLoader
from app.core.config import settings

env = Environment(loader=FileSystemLoader("app/templates/emails"), autoescape=True)


def _render_template(body):
    template_name = body.pop("template")
    template = env.get_template(f"{template_name}.html")
    return template.render(**body)


async def send_email(to, subject, body):
    from email.message import EmailMessage

    html = _render_template(body)

    msg = EmailMessage()
    msg["From"] = settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(html, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_pass,
        start_tls=True,
    )
