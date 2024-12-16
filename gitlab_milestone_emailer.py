import requests
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuration
GITLAB_URL = "https://gitlab.com"  # Change to your GitLab instance URL if self-hosted
PERSONAL_ACCESS_TOKEN = "your_gitlab_personal_access_token"
PROJECT_ID = "your_project_id"
MILESTONE_NAME = "your_milestone_name"

SMTP_SERVER = "smtp.gmail.com"  # Example for Gmail
SMTP_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_email_password"

def get_issues_for_milestone():
    headers = {"PRIVATE-TOKEN": PERSONAL_ACCESS_TOKEN}
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/issues"
    params = {"milestone": MILESTONE_NAME, "state": "all", "per_page": 100}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch issues: {response.status_code} - {response.text}")
    
    issues = response.json()
    return issues

def format_issues_to_table(issues):
    data = []
    for idx, issue in enumerate(issues, 1):
        assignees = [assignee["username"] for assignee in issue.get("assignees", [])]
        data.append({
            "Serial No": idx,
            "Assignee": ", ".join(assignees) if assignees else "Unassigned",
            "Title": issue["title"],
            "Labels": ", ".join(issue.get("labels", []))
        })
    return pd.DataFrame(data)

def send_email(issue_table, recipients):
    # Convert DataFrame to HTML
    issue_table_html = issue_table.to_html(index=False, border=0)

    # Prepare Email
    subject = f"Issues for Milestone: {MILESTONE_NAME}"
    body = f"""
    <html>
    <body>
        <p>Hi,</p>
        <p>Here are the issues tagged to the milestone <b>{MILESTONE_NAME}</b>:</p>
        {issue_table_html}
        <p>Regards,<br>Your GitLab Bot</p>
    </body>
    </html>
    """
    
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Attach the HTML body
    msg.attach(MIMEText(body, "html"))

    # Send Email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())

def main():
    try:
        issues = get_issues_for_milestone()
        if not issues:
            print("No issues found for the milestone.")
            return

        issue_table = format_issues_to_table(issues)
        print(issue_table)

        # Extract unique email addresses of assignees
        recipients = set()
        for issue in issues:
            for assignee in issue.get("assignees", []):
                if "email" in assignee:
                    recipients.add(assignee["email"])

        if not recipients:
            print("No assignees have emails associated.")
            return

        send_email(issue_table, list(recipients))
        print("Email sent successfully to:", recipients)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
