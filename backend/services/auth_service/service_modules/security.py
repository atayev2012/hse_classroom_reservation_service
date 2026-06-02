from email_validator import validate_email, EmailNotValidError
import logging
from datetime import datetime, timezone, timedelta
import random

from service_modules.config import jwt_config, JWTToken

logger = logging.getLogger(__name__)

# email verification function
async def email_validate(email: str) -> bool:
    allowed_domains = ["edu.hse.ru", "hse.ru"]

    try:
        email_info = validate_email(email, check_deliverability=False)

        # Checking if login is performed through proper email
        is_allowed = email_info.domain in allowed_domains
        
        if not is_allowed:
            logger.info(f"@{email_info.domain} is not acceptable")

        return is_allowed
    except EmailNotValidError as e:
        logger.info(f"{email} is in bad format: {e}")
        return False


# random verification code generator
async def generate_verification_code() -> str:
    return str(random.randint(100000, 999999))


if __name__ == "__main__":
    payload = {
        "id": "123456",
        "role": "admin"
    }

    new_token = JWTToken()
    new_token.generate_token(payload)
    print(f"The token created is {new_token.token}")
    print()
    old_token = JWTToken()
    old_token.decode_from_token(new_token.token)
    print(f"The token {old_token.token}\nis_valid: {old_token.is_valid}\nis_expired: {old_token.is_expired}")
