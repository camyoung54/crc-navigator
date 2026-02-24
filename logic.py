from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def calculate_age(dob):
    """Calculate age from date of birth"""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def compute_next_due_date(last_screen_date, last_screen_type, risk_level='standard'):
    """
    Calculate next due date based on screening type and guidelines
    
    CRC Screening Guidelines:
    - Colonoscopy: 10 years (standard risk), 5 years (high risk)
    - FIT (Fecal Immunochemical Test): 1 year
    - Cologuard: 3 years
    - Sigmoidoscopy: 5 years
    - CT Colonography: 5 years
    """
    if not last_screen_date:
        return date.today()  # Never screened - due now
    
    # Screening intervals based on type
    intervals = {
        'Colonoscopy': 10 if risk_level == 'standard' else 5,
        'FIT': 1,
        'Cologuard': 3,
        'Sigmoidoscopy': 5,
        'CT Colonography': 5
    }
    
    interval_years = intervals.get(last_screen_type, 1)
    return last_screen_date + relativedelta(years=interval_years)

def compute_status(next_due_date, last_screen_date=None):
    """
    Determine patient status based on next due date
    
    Status Categories:
    - Never Screened: No previous screening
    - Critically Overdue: More than 1 year past due
    - Overdue: Past the due date
    - Due Soon: Within 90 days of due date
    - Not Due: More than 90 days until due
    """
    if not last_screen_date:
        return "Never Screened"
    
    today = date.today()
    days_until_due = (next_due_date - today).days
    
    if days_until_due < -365:
        return "Critically Overdue"
    elif days_until_due < 0:
        return "Overdue"
    elif days_until_due <= 90:
        return "Due Soon"
    else:
        return "Not Due"

def compute_priority_score(patient_dict):
    """
    Calculate priority score (0-100, higher = more urgent)
    
    This is a rule-based system that could be replaced with ML in the future.
    
    Factors:
    - Never screened: +50 points
    - Days overdue: up to +40 points
    - Age 50-75 (target range): +20 points
    - High risk: +20 points
    """
    score = 0
    today = date.today()
    
    # Never screened - highest priority
    if not patient_dict.get('last_screen_date'):
        score += 50
    else:
        # Days overdue (cap at 40 points)
        days_overdue = (today - patient_dict['next_due_date']).days
        if days_overdue > 0:
            score += min(days_overdue / 10, 40)
    
    # Age factor (50-75 is target screening age range)
    age = patient_dict.get('age', 0)
    if 50 <= age <= 75:
        score += 20
    elif age > 75:
        score += 10  # Still important but lower priority
    
    # Risk level
    if patient_dict.get('risk_level') == 'high':
        score += 20
    
    return min(int(score), 100)

def days_overdue(next_due_date):
    """
    Calculate how many days a patient is overdue
    Returns 0 if not overdue
    """
    if not next_due_date:
        return 0
    
    today = date.today()
    days = (today - next_due_date).days
    return max(days, 0)

def update_patient_computed_fields(session, patient):
    """
    Update all computed fields for a patient
    
    This should be called whenever:
    - A new screening is recorded
    - Patient data is updated
    - Running a batch update on all patients
    """
    # Calculate age from DOB
    patient.age = calculate_age(patient.dob)
    
    # Calculate next due date
    patient.next_due_date = compute_next_due_date(
        patient.last_screen_date,
        patient.last_screen_type,
        patient.risk_level
    )
    
    # Update status
    patient.status = compute_status(patient.next_due_date, patient.last_screen_date)
    
    session.commit()

def get_screening_recommendation(patient):
    """
    Get a human-readable screening recommendation for a patient
    
    Returns a dictionary with recommendation details
    """
    if not patient.last_screen_date:
        return {
            'message': f'{patient.name} has never been screened. Recommend discussing screening options.',
            'urgency': 'High',
            'suggested_action': 'Contact patient to discuss screening options and schedule FIT or colonoscopy'
        }
    
    status = patient.status
    days_left = (patient.next_due_date - date.today()).days
    
    if status == 'Critically Overdue':
        return {
            'message': f'{patient.name} is {abs(days_left)} days overdue for screening.',
            'urgency': 'Critical',
            'suggested_action': 'Priority outreach needed. Contact immediately to schedule screening.'
        }
    elif status == 'Overdue':
        return {
            'message': f'{patient.name} is {abs(days_left)} days overdue for screening.',
            'urgency': 'High',
            'suggested_action': 'Contact patient to schedule screening as soon as possible.'
        }
    elif status == 'Due Soon':
        return {
            'message': f'{patient.name} is due for screening in {days_left} days.',
            'urgency': 'Medium',
            'suggested_action': 'Contact patient to schedule screening in advance.'
        }
    else:
        return {
            'message': f'{patient.name} is not due for screening until {patient.next_due_date.strftime("%m/%d/%Y")}.',
            'urgency': 'Low',
            'suggested_action': 'No action needed at this time.'
        }