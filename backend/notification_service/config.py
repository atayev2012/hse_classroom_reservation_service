from os import getenv
from dotenv import load_dotenv

load_dotenv()

class NotificationServiceConfiguration:
    def __init__(self):
        self.host = getenv("NOTIFICATION_HOST")
        self.port = int(getenv("NOTIFICATION_PORT"))

class EmailConfiguration:
    def __init__(self):
        self.host = getenv("EMAIL_HOST")
        self.port = int(getenv("EMAIL_PORT"))
        self.username = getenv("EMAIL_USERNAME")
        self.password = getenv("EMAIL_PASSWORD")
        self.from_email = getenv("EMAIL_ADDRESS")
        self.use_tls = getenv("EMAIL_USE_TLS").lower() in ["true", "1", "yes"]

        # verification code variables (vc)
        self.vc_subject = "Подтверждение входа в систему бронирования аудиторий НИУ ВШЭ - НН"

        
config = NotificationServiceConfiguration()
email_config = EmailConfiguration()

if __name__ == "__main__":
    print(f"The host = {config.host}")
    print(f"The port = {config.port}")
