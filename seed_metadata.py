from app import create_app, db
from app.models.models import Race, MaritalStatus, Occupation, ReferringDoctorHospital, Consultant, Pharmacy

def seed_metadata():
    app = create_app()
    with app.app_context():
        # Races
        races = ['African', 'Asian', 'Caucasian', 'Hispanic', 'Other', 'Not Applicable']
        for r in races:
            if not Race.query.filter_by(name=r).first():
                db.session.add(Race(name=r))

        # Marital Status
        statuses = ['Single', 'Married', 'Divorced', 'Widowed', 'Not Applicable']
        for s in statuses:
            if not MaritalStatus.query.filter_by(name=s).first():
                db.session.add(MaritalStatus(name=s))

        # Occupations
        occupations = ['Employed', 'Self-Employed', 'Unemployed', 'Student', 'Retired', 'Not Applicable']
        for o in occupations:
            if not Occupation.query.filter_by(name=o).first():
                db.session.add(Occupation(name=o))

        # Referring Doctors / Hospitals
        referrers = [
            {'name': 'General Hospital', 'type': 'Hospital'},
            {'name': 'Dr. Smith Clinic', 'type': 'Doctor'},
            {'name': 'Not Applicable', 'type': 'Hospital'}
        ]
        for ref in referrers:
            if not ReferringDoctorHospital.query.filter_by(name=ref['name']).first():
                db.session.add(ReferringDoctorHospital(name=ref['name'], type=ref['type']))

        # Consultants
        consultants = ['Dr. John Doe', 'Dr. Jane Smith', 'Not Applicable']
        for c in consultants:
            if not Consultant.query.filter_by(name=c).first():
                db.session.add(Consultant(name=c))

        # Pharmacies
        pharmacies = ['Main Pharmacy', 'External Pharmacy', 'Not Applicable']
        for p in pharmacies:
            if not Pharmacy.query.filter_by(name=p).first():
                db.session.add(Pharmacy(name=p))

        db.session.commit()
        print("Metadata seeded successfully!")

if __name__ == '__main__':
    seed_metadata()
