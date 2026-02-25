from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    
    id = Column(Integer, primary_key=True)
    mrn = Column(String, unique=True)
    name = Column(String)
    dob = Column(Date)
    age = Column(Integer)
    village = Column(String)
    phone = Column(String)
    email = Column(String)
    
    # Screening history
    last_screen_date = Column(Date)
    last_screen_type = Column(String)
    next_due_date = Column(Date)
    
    # Risk factors (UPDATED)
    family_history_crc = Column(Boolean, default=False)
    major_comorbidities = Column(Boolean, default=False)
    
    # Status and tracking
    status = Column(String)
    language = Column(String)
    interpreter_needed = Column(Boolean, default=False)
    transportation_barrier = Column(Boolean, default=False)
    last_contact_date = Column(Date)
    notes = Column(Text)

class Contact(Base):
    __tablename__ = 'contacts'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    timestamp = Column(DateTime, default=datetime.now)
    method = Column(String)
    outcome = Column(String)
    user = Column(String)
    role = Column(String)
    notes = Column(Text)

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey('patients.id'))
    
    # Task details
    task_type = Column(String)  # From TASK_TYPES list
    description = Column(Text)
    
    # Assignment
    assigned_to = Column(String)  # Person's name
    assigned_role = Column(String)  # Navigator, PCP, Specialist, etc.
    
    # Status tracking
    status = Column(String, default='Pending')  # Pending, In Progress, Completed, Cancelled
    priority = Column(String, default='Medium')  # Low, Medium, High, Urgent
    
    # Dates
    created_date = Column(DateTime, default=datetime.now)
    due_date = Column(Date)
    completed_date = Column(DateTime)
    
    # Tracking
    created_by = Column(String)
    created_by_role = Column(String)
    notes = Column(Text)