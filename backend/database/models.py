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


# University building
class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String, nullable=False)

    # relationships
    rooms: Mapped[list["BuildingRoom"]] = relationship(back_populates="building")

# Room in the building
class BuildingRoom(Base):
    __tablename__ = "building_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    type: Mapped[str] = mapped_column(String, nullable=False, default="classroom")
    floor: Mapped[int] = mapped_column(Integer, nullable=True)

    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id"))

    # relationships
    building: Mapped["Building"] = relationship(back_populates="rooms")
    equipment: Mapped[list["BuildingRoomEquipment"]] = relationship(back_populates="room")
    
# Equipment that room conrains
class BuildingRoomEquipment(Base):
    __tablename__ = "building_room_equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    room_id: Mapped[int] = mapped_column(ForeignKey("building_rooms.id"))

    # relationships
    room: Mapped["BuildingRoom"] = relationship(back_populates="equipment")

