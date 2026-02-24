from db import init_db, get_session, add_patient
from logic import update_patient_computed_fields
from datetime import date, timedelta
import random

def create_demo_data():
    """Create realistic fake patient data for demo"""
    
    # Maniilaq Health Center villages
    villages = [
        'Kotzebue', 'Kivalina', 'Noatak', 'Point Hope', 'Kiana',
        'Noorvik', 'Selawik', 'Ambler', 'Shungnak', 'Kobuk', 
        'Deering', 'Buckland', 'Kotzebue', 'Kotzebue', 'Kotzebue'
    ]
    
    first_names = [
    'John', 'Mary', 'James', 'Patricia', 'Robert', 'Jennifer', 
    'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Susan',
    'Richard', 'Jessica', 'Joseph', 'Sarah', 'Thomas', 'Karen',
    'Charles', 'Nancy', 'Daniel', 'Lisa', 'Matthew', 'Betty',
    # Additional Alaska Native names
    'Annie', 'Lucy', 'Moses', 'Peter', 'Paul', 'Charlie',
    'George', 'Martha', 'Sophie', 'Frank', 'Henry', 'Emma',
    'Abraham', 'Margaret', 'Ruth', 'Andrew', 'Helen', 'Isaac'
    ]

    last_names = [
    'Smith', 'Jones', 'Williams', 'Brown', 'Davis', 'Miller',
    'Wilson', 'Moore', 'Taylor', 'Anderson', 'Thomas', 'Jackson',
    'White', 'Harris', 'Martin', 'Thompson', 'Garcia', 'Martinez',
    'Robinson', 'Clark', 'Rodriguez', 'Lewis', 'Lee', 'Walker',
    # Additional Alaska Native surnames
    'Alexie', 'Charlie', 'Nick', 'Pete', 'Paul', 'Carl',
    'Attla', 'Moses', 'Isaac', 'George', 'Andrew', 'Hunter',
    'Active', 'Lincoln', 'Washington', 'Jefferson', 'Bird', 'Fox',
    'Black', 'Raven', 'Bear', 'Ivan', 'John', 'Sam'
    ]
    
    # Screening types
    screen_types = ['Colonoscopy', 'FIT', 'Cologuard', None]
    
    # Languages spoken in the region
    languages = ['English', 'Iñupiaq', 'English', 'English']  # Weighted toward English
    
    session = get_session()
    
    print("\n🏥 Creating demo patients for Maniilaq CRC Screening Program...")
    print("=" * 60)
    
    for i in range(342):
        # Random age between 20-90 (screening age range is 45-75)
        age = random.randint(20, 90)
        dob = date.today() - timedelta(days=age*365 + random.randint(0, 365))
        
        # Random last screening (or none)
        # 30% never screened, 70% have been screened
        if random.random() < 0.3:
            last_screen_type = None
            last_screen_date = None
        else:
            last_screen_type = random.choice(['Colonoscopy', 'FIT', 'Cologuard'])
            # Screened somewhere between 0-15 years ago
            days_ago = random.randint(0, 15*365)
            last_screen_date = date.today() - timedelta(days=days_ago)
        
        # 15% high risk
        risk_level = 'high' if random.random() < 0.25 else 'standard'
        
        # 20% have transportation barriers
        transportation_barrier = random.random() < 0.30
        
        # Generate patient data
        patient_data = {
            'mrn': str(random.randint(1000000, 9999999)),
            'name': f'{random.choice(first_names)} {random.choice(last_names)}',
            'dob': dob,
            'age': age,
            'village': random.choice(villages),
            'phone': f'907-555-{random.randint(1000,9999)}',
            'email': f'patient{i}@example.com' if random.random() < 0.5 else None,
            'language': random.choice(languages),
            'last_screen_date': last_screen_date,
            'last_screen_type': last_screen_type,
            'risk_level': risk_level,
            'transportation_barrier': transportation_barrier,
            'notes': 'Demo patient' if random.random() < 0.3 else None
        }
        
        # Add patient to database
        patient = add_patient(session, patient_data)
        
        # Calculate computed fields (next_due_date, status)
        update_patient_computed_fields(session, patient)
        
        # Print progress
        status_emoji = {
            'Never Screened': '🔴',
            'Critically Overdue': '🔴',
            'Overdue': '🟠',
            'Due Soon': '🟡',
            'Not Due': '🟢'
        }
        emoji = status_emoji.get(patient.status, '⚪')
        
        print(f"{emoji} Created: {patient.name:25} | {patient.village:12} | {patient.status}")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("📊 SUMMARY STATISTICS")
    print("=" * 60)
    
    from db import get_all_patients
    patients = get_all_patients(session)
    
    total = len(patients)
    never_screened = len([p for p in patients if p.status == 'Never Screened'])
    critically_overdue = len([p for p in patients if p.status == 'Critically Overdue'])
    overdue = len([p for p in patients if p.status == 'Overdue'])
    due_soon = len([p for p in patients if p.status == 'Due Soon'])
    not_due = len([p for p in patients if p.status == 'Not Due'])
    high_risk = len([p for p in patients if p.risk_level == 'high'])
    
    print(f"\n📋 Total Patients: {total}")
    print(f"\n🎯 Status Breakdown:")
    print(f"   🔴 Never Screened: {never_screened} ({never_screened/total*100:.1f}%)")
    print(f"   🔴 Critically Overdue: {critically_overdue} ({critically_overdue/total*100:.1f}%)")
    print(f"   🟠 Overdue: {overdue} ({overdue/total*100:.1f}%)")
    print(f"   🟡 Due Soon: {due_soon} ({due_soon/total*100:.1f}%)")
    print(f"   🟢 Not Due: {not_due} ({not_due/total*100:.1f}%)")
    print(f"\n⚠️  High Risk Patients: {high_risk} ({high_risk/total*100:.1f}%)")
    
    # Village breakdown
    print(f"\n🏘️  Patients by Village:")
    village_counts = {}
    for p in patients:
        village_counts[p.village] = village_counts.get(p.village, 0) + 1
    
    for village in sorted(village_counts.keys()):
        print(f"   {village:15} {village_counts[village]:2} patients")
    
    print("\n" + "=" * 60)
    print("✅ Demo data creation complete!")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🚀 Initializing CRC Navigator Database...")
    init_db()
    print("\n")
    create_demo_data()
    print("\n✨ Database is ready! You can now run the Streamlit app.\n")