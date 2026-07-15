# app/core/notifications.py

# TODO: import settings (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS) from config
# TODO: import an async SMTP library (e.g. aiosmtplib) — not stdlib smtplib, that's sync
# TODO: import Jinja2 (Environment, FileSystemLoader or PackageLoader)

# TODO: set up Jinja2 environment — loader pointing at app/templates/emails/
# TODO: one template file per email type, or one generic template with a body block

# TODO: define async def send_email(to, subject, body)
# TODO: build the email message (subject, from, to, body) — email.message.EmailMessage
# TODO: connect + send via aiosmtplib using settings above

# TODO: define render helper — takes template name + context dict, returns rendered string
# TODO: decide: does send_email's `body` param take pre-rendered text, or template name + context?
