from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Patient, Contact
import os

DATABASE_URL = "sqlite:///crc_navigator_v2.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized!")

def get_session():
    """Get a new database session"""
    return SessionLocal()

def add_patient(session, patient_data):
    """Add a new patient to the database"""
    patient = Patient(**patient_data)
    session.add(patient)
    session.commit()
    return patient

def get_all_patients(session):
    """Get all patients from the database"""
    return session.query(Patient).all()

def get_patient_by_id(session, patient_id):
    """Get a specific patient by their ID"""
    return session.query(Patient).filter(Patient.id == patient_id).first()

def update_patient(session, patient_id, updates):
    """Update a patient's information"""
    patient = get_patient_by_id(session, patient_id)
    if patient:
        for key, value in updates.items():
            setattr(patient, key, value)
        session.commit()
    return patient

def add_contact(session, contact_data):
    """Add a new contact log entry"""
    contact = Contact(**contact_data)
    session.add(contact)
    session.commit()
    return contact

def get_patient_contacts(session, patient_id):
    """Get all contact logs for a specific patient"""
    return session.query(Contact).filter(
        Contact.patient_id == patient_id
    ).order_by(Contact.timestamp.desc()).all()

def update_patient_status(session, patient_id, new_status):
    """Update a patient's status"""
    patient = get_patient_by_id(session, patient_id)
    if patient:
        patient.status = new_status
        session.commit()
    return patient