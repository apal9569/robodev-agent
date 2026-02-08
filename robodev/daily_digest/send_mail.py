import json
import http.client
import urllib.request
from pathlib import Path

CONFIG_PATH = Path.home() / ".robodev" / "mail_config.json"


def load_mail_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Mail config not found. Create {CONFIG_PATH} with:\n"
            + json.dumps({
                "provider": "resend",
                "api_key": "re_xxxxxxxxxxxx",
                "sender_email": "digest@yourdomain.com",
                "recipient_email": "your-email@gmail.com",
            }, indent=2)
            + "\n\nOr for SMTP:\n"
            + json.dumps({
                "provider": "smtp",
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "you@gmail.com",
                "sender_password": "app-password",
                "recipient_email": "you@gmail.com",
            }, indent=2)
        )
    return json.loads(CONFIG_PATH.read_text())


def send_digest_email(subject: str, body_markdown: str):
    config = load_mail_config()
    provider = config.get("provider", "smtp")

    if provider == "resend":
        _send_via_resend(config, subject, body_markdown)
    elif provider == "smtp":
        _send_via_smtp(config, subject, body_markdown)
    else:
        raise ValueError(f"Unknown mail provider: {provider}")


def _send_via_resend(config: dict, subject: str, body_markdown: str):
    html_body = _markdown_to_simple_html(body_markdown)
    payload = json.dumps({
        "from": config["sender_email"],
        "to": [config["recipient_email"]],
        "subject": subject,
        "html": html_body,
        "text": body_markdown,
    })

    conn = http.client.HTTPSConnection("api.resend.com", timeout=30)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['api_key']}",
    }
    conn.request("POST", "/emails", body=payload, headers=headers)
    resp = conn.getresponse()
    resp_body = resp.read().decode()  # FIX: was `body` which shadows `body_markdown` usage
    conn.close()

    if resp.status >= 400:
        raise RuntimeError(f"Resend API error {resp.status}: {resp_body}")

    result = json.loads(resp_body)
    print(f"📧 Digest emailed to {config['recipient_email']} (id: {result.get('id', 'ok')})")


def _send_via_smtp(config: dict, subject: str, body_markdown: str):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["sender_email"]
    msg["To"] = config["recipient_email"]

    msg.attach(MIMEText(body_markdown, "plain"))
    msg.attach(MIMEText(_markdown_to_simple_html(body_markdown), "html"))

    with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
        server.starttls()
        server.login(config["sender_email"], config["sender_password"])
        server.sendmail(config["sender_email"], config["recipient_email"], msg.as_string())
    print(f"📧 Digest emailed to {config['recipient_email']}")


def _markdown_to_simple_html(md: str) -> str:
    import re
    lines = md.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("# "):
            line = f"<h1>{line[2:]}</h1>"
        elif line.startswith("## "):
            line = f"<h2>{line[3:]}</h2>"
        elif line.startswith("> "):
            line = f"<blockquote>{line[2:]}</blockquote>"
        else:
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
            if line.strip():
                line = f"<p>{line}</p>"
            else:
                line = "<br>"
        html_lines.append(line)
    return f"""<html><body style="font-family: sans-serif; max-width: 700px; margin: auto; padding: 20px;">
{''.join(html_lines)}
</body></html>"""

