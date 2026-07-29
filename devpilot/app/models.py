from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Relationships with staff awards and marks
    staff_awards = relationship("StaffAward", back_populates="student")
    marks = relationship("Mark", back_populates="student")

class StaffAward(Base):
    __tablename__ = "staff_awards"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staffs.id"), nullable=False)

    # Relationships with marks and staff
    mark = relationship("Mark", back_populates="award")
    staff = relationship("Staff", back_populates="awards")

class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staffs.id"), nullable=False)

    # Relationships with marks and staff
    award = relationship("StaffAward", back_populates="mark")
    staff = relationship("Staff", back_populates="marks")

class Staff(Base):
    __tablename__ = "staffs"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)

    # Relationships with marks and awards
    marks = relationship("Mark", back_populates="staff")
    awards = relationship("StaffAward", back_populates="staff")

# Sample data insertion (not part of the model but for testing purposes)
def insert_sample_data():
    staffs = [
        {"name": "Alice"},
        {"name": "Bob"}
    ]

    marks = [
        {"student_id": 1, "staff_id": 2},
        {"student_id": 3, "staff_id": 4}
    ]

    awards = [
        {"staff_id": 2, "award_id": 1},
        {"staff_id": 4, "award_id": 2}
    ]

    for staff in staffs:
        Staff(name=staff["name"]).save()

    for mark in marks:
        Mark(student_id=mark["student_id"], staff_id=mark["staff_id"]).save()

    for award in awards:
        StaffAward(staff_id=award["staff_id"], award_id=award["award_id"]).save()