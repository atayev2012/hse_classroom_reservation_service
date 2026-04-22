import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import email_config, EmailConfiguration

# Email verification function
def send_verification_email(
    to_email: str,
    verification_code: str,
    verify_url: str,
    email_config: EmailConfiguration = email_config
) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = email_config.vc_subject
    message["From"] = email_config.from_email
    message["To"] = to_email

    html_body = laod_email_body("templates/verification_code.html")
    html_body = html_body.replace("{verification_code}", verification_code)
    html_body = html_body.replace("{user_email}", to_email)
    html_body = html_body.replace("{confirm_url}", verify_url)

    message.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(email_config.host, email_config.port) as server:
        if email_config.use_tls:
            server.starttls()
        server.login(email_config.username, email_config.password)
        server.sendmail(
            email_config.from_email,
            to_email,
            message.as_string()
        )

def laod_email_body(filename: str) -> str:
    with open(filename, "rt", encoding="utf-8") as file:
        template = file.read()
    
    return template


# if __name__ == "__main__":
#     send_verification_email(
#         "atayev2012@gmail.com",
#         "124300",
#         "https://github.com/atayev2012"
#     )
