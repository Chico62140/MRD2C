from sqlalchemy.orm import Session
from . import models
import os
import shutil
import json
import smtplib
from email.mime.text import MIMEText


def get_requests(db: Session):
    return db.query(models.Request).all()


def create_request(db: Session, request):
    db_request = models.Request(**request.dict(), status="pending")
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request


def update_status(db: Session, request_id: int, new_status: str):
    req = db.query(models.Request).filter(models.Request.id == request_id).first()
    if req:
        req.status = new_status
        db.commit()
        handle_post_status_action(req, new_status)
    return req


def handle_post_status_action(req, status):
    try:
        with open("app/settings.json") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"Failed to load settings.json: {e}")
        return

    drive_mappings = settings.get("drive_mappings", {})
    group_destinations = settings.get("group_destinations", {})

    # Determine source base from matching drive mapping key
    base_drive_path = None
    for key, path in drive_mappings.items():
        if key.lower() in req.path.lower():
            base_drive_path = path
            break

    # Fallback to first entry
    if not base_drive_path and drive_mappings:
        base_drive_path = list(drive_mappings.values())[0]

    # Determine destination
    group_key = next((k for k in group_destinations if k.lower() in req.name.lower()), None)
    output_path = group_destinations.get(group_key) if group_key else next(iter(group_destinations.values()), None)

    if not base_drive_path or not output_path:
        print("Could not resolve source or destination path from settings.")
        return

    source = os.path.join(base_drive_path, req.path, req.filename)
    dest = os.path.join(output_path, req.filename)

    if status == "approved":
        try:
            if os.path.isdir(source):
                shutil.copytree(source, dest, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)
            print(f"Moved: {source} → {dest}")
        except Exception as e:
            print(f"Error moving file/folder: {e}")

    elif status == "denied":
        send_denial_email(req.name, settings.get("email_info", {}))


def send_denial_email(user_email, email_config):
    try:
        msg = MIMEText(email_config.get("body", "Your request has been denied."))
        msg["Subject"] = email_config.get("subject", "Request Update")
        msg["From"] = email_config.get("from", "noreply@example.com")
        msg["To"] = user_email

        server = smtplib.SMTP(email_config.get("smtp_server"), email_config.get("smtp_port"))
        server.starttls()
        server.login(email_config.get("smtp_user"), email_config.get("smtp_password"))
        server.sendmail(msg["From"], [msg["To"]], msg.as_string())
        server.quit()
        print(f"Denial email sent to {user_email}")
    except Exception as e:
        print(f"Email error: {e}")
