from database import Base
from sqlalchemy import BigInteger, String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


# User model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    
    # Level 1: Student; Level 2: Employee; Level 3: Manager; Level 4: Admin
    type: Mapped[str] = mapped_column(String, nullable=False)
    
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # relationships
    user_verification: Mapped["UserVerification"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
 

# Verification code model
class UserVerification(Base):
    __tablename__ = "user_verifications"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    verification_code: Mapped[str] = mapped_column(String, nullable=True)

    # relationships
    user: Mapped["User"] = relationship(back_populates="user_verification")




