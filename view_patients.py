from db import get_session, get_all_patients
from datetime import date

session = get_session()
patients = get_all_patients(session)[:3]

print("\n" + "="*80)
print("FIRST 3 PATIENTS - COMPLETE DATA STRUCTURE")
print("="*80)

for i, p in enumerate(patients, 1):
    print(f"\n{'='*80}")
    print(f"PATIENT #{i}")
    print(f"{'='*80}")
    print(f"ID:                      {p.id}")
    print(f"MRN:                     {p.mrn}")
    print(f"Name:                    {p.name}")
    print(f"Date of Birth:           {p.dob}")
    print(f"Age:                     {p.age}")
    print(f"Village:                 {p.village}")
    print(f"Phone:                   {p.phone}")
    print(f"Email:                   {p.email}")
    print(f"Language:                {p.language}")
    print(f"Transportation Barrier:  {p.transportation_barrier}")
    print(f"\n--- SCREENING HISTORY ---")
    print(f"Last Screen Date:        {p.last_screen_date}")
    print(f"Last Screen Type:        {p.last_screen_type}")
    print(f"Next Due Date:           {p.next_due_date}")
    print(f"Status:                  {p.status}")
    print(f"Risk Level:              {p.risk_level}")
    print(f"\n--- ADDITIONAL ---")
    print(f"Notes:                   {p.notes}")
    print(f"Last Contact Date:       {p.last_contact_date}")
    
    # Calculate days overdue if applicable
    if p.next_due_date:
        days_diff = (date.today() - p.next_due_date).days
        if days_diff > 0:
            print(f"\n⚠️  DAYS OVERDUE:          {days_diff}")
        else:
            print(f"\n✅ Days until due:         {abs(days_diff)}")

print("\n" + "="*80 + "\n")