from app import create_app, db, bcrypt
from app.models.models import (Role, Ward, User, Race, MaritalStatus, Occupation, 
                               ReferringDoctorHospital, Consultant, Pharmacy)

def seed():
    app = create_app()
    with app.app_context():
        # Roles
        roles = ['Admin', 'CMO', 'Sister In Charge', 'Nurse', 'Executive']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))

        # Wards
        wards = [
            {'name': 'Admission Ward A', 'type': 'Admission', 'capacity': 20},
            {'name': 'Admission Ward B', 'type': 'Admission', 'capacity': 20},
            {'name': 'Admission Ward C', 'type': 'Admission', 'capacity': 20},
            {'name': 'Discharge Ward', 'type': 'Discharge', 'capacity': 30},
            {'name': 'General Ward 1', 'type': 'General', 'capacity': 50},
            {'name': 'General Ward 2', 'type': 'General', 'capacity': 50},
        ]
        for w in wards:
            if not Ward.query.filter_by(name=w['name']).first():
                db.session.add(Ward(name=w['name'], type=w['type'], capacity=w['capacity']))

        # Races
        races = [
            'African', 'Caucasian', 'Asian', 'Arab', 'Indian', 'Mixed', 'Other'
        ]
        for race_name in races:
            if not Race.query.filter_by(name=race_name).first():
                db.session.add(Race(name=race_name))

        # Marital Statuses
        statuses = ['Single', 'Married', 'Divorced', 'Widowed', 'Separated']
        for status_name in statuses:
            if not MaritalStatus.query.filter_by(name=status_name).first():
                db.session.add(MaritalStatus(name=status_name))

        # Occupations
        occupations = [
            'Farmer', 'Teacher', 'Healthcare Worker', 'Business Owner', 'Laborer', 
            'Student', 'Retired', 'Unemployed', 'Housewife', 'Artisan', 'Driver', 
            'Government Official', 'Engineer', 'Other'
        ]
        for occ_name in occupations:
            if not Occupation.query.filter_by(name=occ_name).first():
                db.session.add(Occupation(name=occ_name))

        # Referring Doctors/Hospitals
        referrers = [
            {'name': 'Dr. John Kabuye', 'type': 'Doctor'},
            {'name': 'Dr. Jane Okoro', 'type': 'Doctor'},
            {'name': 'Dr. Peter Asiimwe', 'type': 'Doctor'},
            {'name': 'Dr. Mary Nakamatte', 'type': 'Doctor'},
            {'name': 'Mulago Hospital', 'type': 'Hospital'},
            {'name': 'Kampala International Hospital', 'type': 'Hospital'},
            {'name': 'Case Medical Centre', 'type': 'Hospital'},
            {'name': 'Nsambya Hospital', 'type': 'Hospital'},
        ]
        for ref in referrers:
            if not ReferringDoctorHospital.query.filter_by(name=ref['name']).first():
                db.session.add(ReferringDoctorHospital(name=ref['name'], type=ref['type']))

        # Consultants
        consultants = [
            'Dr. Paul Atim', 'Dr. Elizabeth Okello', 'Dr. David Mwase', 
            'Dr. Sarah Njoroge', 'Dr. Joseph Mwebaze', 'Dr. Grace Kamau'
        ]
        for consul_name in consultants:
            if not Consultant.query.filter_by(name=consul_name).first():
                db.session.add(Consultant(name=consul_name))

        # Pharmacies
        pharmacies = [
            'Main Hospital Pharmacy', 'Ward A Pharmacy', 'Ward B Pharmacy', 
            'Emergency Pharmacy', 'Outpatient Pharmacy'
        ]
        for pharm_name in pharmacies:
            if not Pharmacy.query.filter_by(name=pharm_name).first():
                db.session.add(Pharmacy(name=pharm_name))

        db.session.commit()

        # Admin User
        admin_role = Role.query.filter_by(name='Admin').first()
        if not User.query.filter_by(email='admin@hospital.com').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin_user = User(name='Admin User', email='admin@hospital.com', password_hash=hashed_pw, role_id=admin_role.id)
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created.")

if __name__ == '__main__':
    seed()
    print("Database seeded!")
