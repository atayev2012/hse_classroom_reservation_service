from os import getenv
from dotenv import load_dotenv

load_dotenv()

class APIConfiguration:
    def __init__(self):
        self.auth_port = int(getenv("AUTH_PORT"))
        self.notification_port = int(getenv("NOTIFICATION_PORT"))

config = APIConfiguration()
