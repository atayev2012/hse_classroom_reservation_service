from database import Base
from sqlalchemy import Column, Integer, BigInteger, String, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship


# User model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Level 1: Student; Level 2: Employee; Level 3: Manager; Level 4: Admin
    access_level: Mapped[int] = mapped_column(Integer, nullable=False)
    
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)
    user_img: Mapped[str] = mapped_column(String(255), nullable=True)
 

class UserVerification(Base):
    __table_name__ = "user_verifications"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), unique=True)
    verification_code: Mapped[str] = mapped_column(String(6), nullable=True)
