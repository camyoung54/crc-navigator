from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    mrn = Column(String(50))
    name = Column(String(100), nullable=False)
    dob = Column(Date, nullable=False)
    age = Column(Integer)
    village = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100))
    last_screen_date = Column(Date)
    last_screen_type = Column(String(50))  # Colonoscopy, FIT, Cologuard
    next_due_date = Column(Date)
    family_history_crc = Column(Boolean, default=False)  # Family history of colorectal cancer
    major_comorbidities = Column(Boolean, default=False)  # Has major comorbidities
    status = Column(String(50))  # Not due, Due, Overdue, Completed, Declined
    language = Column(String(50))  # English, Iñupiaq, etc.
    interpreter_needed = Column(Boolean, default=False)
    transportation_barrier = Column(Boolean, default=False)
    last_contact_date = Column(Date)  # Auto-update from contacts
    notes = Column(Text)
    
    contacts = relationship("Contact", back_populates="patient")

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    timestamp = Column(DateTime, default=datetime.now)
    method = Column(String(50))  # Phone, Text, In-person, Mail
    outcome = Column(String(100))  # No answer, Reached - scheduled, etc.
    user = Column(String(100))  # Navigator name
    role = Column(String) # Role of person making contact
    notes = Column(Text)
    
    patient = relationship("Patient", back_populates="contacts")