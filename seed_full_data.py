import random
from datetime import datetime, timedelta, date
from app import create_app, db
from app.models.models import Role, User, Ward, Patient, Race, MaritalStatus, Occupation, ReferringDoctorHospital, Consultant, Pharmacy
from werkzeug.security import generate_password_hash

def seed_data():
    app = create_app()
    with app.app_context():
        print("Starting seed process...")

        # 1. Seed Roles
        roles_names = ['Admin', 'CMO', 'Executive', 'Nurse', 'Sister In Charge']
        for role_name in roles_names:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()
        print("Roles seeded.")

        # 2. Seed Wards
        wards_data = [
            {'name': 'Admission Unit A', 'type': 'Admission', 'capacity': 10},
            {'name': 'General Ward 1', 'type': 'General', 'capacity': 20},
            {'name': 'General Ward 2', 'type': 'General', 'capacity': 20},
            {'name': 'Discharge Suite', 'type': 'Discharge', 'capacity': 15}
        ]
        wards = []
        for w_data in wards_data:
            ward = Ward.query.filter_by(name=w_data['name']).first()
            if not ward:
                ward = Ward(name=w_data['name'], type=w_data['type'], capacity=w_data['capacity'])
                db.session.add(ward)
            wards.append(ward)
        db.session.commit()
        print("Wards seeded.")

        # 3. Seed Staff (10)
        roles = Role.query.all()
        staff_names = [
            ('Alice Smith', 'Admin'), ('Bob Johnson', 'CMO'), ('Charlie Brown', 'Nurse'),
            ('Diana Prince', 'Sister In Charge'), ('Edward Norton', 'Nurse'), ('Fiona Gallagher', 'Nurse'),
            ('George Clooney', 'Nurse'), ('Hannah Montana', 'Sister In Charge'), ('Ian McKellen', 'Executive'),
            ('Jenny Forrest', 'Nurse')
        ]
        
        for name, role_name in staff_names:
            email = name.lower().replace(' ', '.') + '@hospital.com'
            if not User.query.filter_by(email=email).first():
                role = Role.query.filter_by(name=role_name).first()
                # Assign Sister in Charge to wards
                ward_id = None
                if role_name == 'Sister In Charge':
                    # Cycle through wards
                    ward_id = wards[random.randint(0, len(wards)-1)].id
                
                user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash('password123'),
                    role_id=role.id,
                    ward_id=ward_id
                )
                db.session.add(user)
        db.session.commit()
        print("Staff seeded.")

        # 4. Seed Patients (30)
        surnames = ['Moyo', 'Sibanda', 'Ndlovu', 'Dube', 'Ncube', 'Phiri', 'Banda', 'Chirwa', 'Mutale', 'Mwanga']
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth']
        addresses = ['123 Main St, Bulawayo', '456 High Rd, Harare', '789 Low Lane, Mutare', '101 Pine St, Gweru']
        
        races = Race.query.all()
        marital_statuses = MaritalStatus.query.all()
        occupations = Occupation.query.all()
        referrers = ReferringDoctorHospital.query.all()
        consultants = Consultant.query.all()
        pharmacies = Pharmacy.query.all()

        for i in range(30):
            hosp_id = str(25000 + i).zfill(6)
            if not Patient.query.filter_by(hospital_id=hosp_id).first():
                surname = random.choice(surnames)
                fname = random.choice(first_names)
                age = random.randint(0, 100)
                
                patient = Patient(
                    hospital_id=hosp_id,
                    surname=surname,
                    first_names=fname,
                    age=age,
                    sex=random.choice(['Male', 'Female']),
                    race=random.choice(races).name if races else 'Other',
                    marital_status=random.choice(marital_statuses).name if marital_statuses else 'Single',
                    occupation=random.choice(occupations).name if occupations else 'Unemployed',
                    religion='Not Applicable',
                    residential_address=random.choice(addresses),
                    contact_number='+2637' + str(random.randint(1000000, 9999999)),
                    employer_name='Self' if random.random() > 0.5 else None,
                    employer_address='N/A',
                    next_of_kin_name='Next of Kin ' + fname,
                    next_of_kin_address=random.choice(addresses),
                    next_of_kin_relationship=random.choice(['Spouse', 'Parent', 'Sibling', 'Child']),
                    chief='N/A',
                    village='N/A',
                    tribe='N/A',
                    admission_datetime=datetime.now() - timedelta(days=random.randint(1, 10)),
                    referring_doctor_hospital=random.choice(referrers).name if referrers else 'General Hospital',
                    diagnosis='Psychosis' if random.random() > 0.5 else 'Bipolar Disorder',
                    doctor_name='Dr. House',
                    consultant_name=random.choice(consultants).name if consultants else 'Dr. John Doe',
                    pharmacy_name=random.choice(pharmacies).name if pharmacies else 'Main Pharmacy',
                    status=random.choice(['Registered', 'Admitted', 'Discharged']),
                    is_deleted=False
                )
                
                # If admitted, assign a ward
                if patient.status == 'Admitted':
                    patient.ward_id = random.choice(wards).id
                elif patient.status == 'Discharged':
                    patient.discharge_datetime = datetime.now()
                
                db.session.add(patient)
        
        db.session.commit()
        print("Patients seeded.")
        print("Seed process completed successfully!")

if __name__ == '__main__':
    seed_data()
