import pytest
from app import create_app, db, bcrypt
from app.models.models import User, Role, Ward, Patient
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed roles
        roles = ['Admin', 'Nurse']
        for role_name in roles:
            db.session.add(Role(name=role_name))

        # Seed wards
        db.session.add(Ward(name='Admission Ward', type='Admission'))
        db.session.add(Ward(name='General Ward', type='General'))

        # Seed lookup tables
        from app.models.models import Race, MaritalStatus, Occupation, ReferringDoctorHospital, Consultant, Pharmacy
        
        for r in ['African', 'Caucasian', 'Asian', 'Other']:
            db.session.add(Race(name=r))
        for m in ['Single', 'Married', 'Divorced', 'Widowed']:
            db.session.add(MaritalStatus(name=m))
        for o in ['Farmer', 'Teacher', 'Student', 'Other']:
            db.session.add(Occupation(name=o))
        db.session.add(ReferringDoctorHospital(name='Dr. Peter Asiimwe', type='Doctor'))
        for c in ['Dr. Paul Atim', 'Dr. David Mwase']:
            db.session.add(Consultant(name=c))
        for p in ['Main Hospital Pharmacy', 'Ward A Pharmacy']:
            db.session.add(Pharmacy(name=p))

        # Seed admin
        admin_role = Role.query.filter_by(name='Admin').first()
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(name='Admin', email='admin@test.com', password_hash=hashed_pw, role_id=admin_role.id)
        db.session.add(admin_user)

        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, email, password):
    return client.post('/auth/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)

def test_register_patient(client, app):
    login(client, 'admin@test.com', 'admin123')
    response = client.post('/patient/register', data=dict(
        surname='Doe',
        first_names='John',
        date_of_birth='1996-05-27',
        sex='Male',
        race=1,
        marital_status=1,
        occupation=1,
        residential_address='123 Main Street, Kampala',
        contact_number='0771234567',
        next_of_kin_name='Jane Doe',
        next_of_kin_address='123 Main Street, Kampala',
        next_of_kin_relationship='Spouse',
        admission_datetime='2026-05-27 13:00',
        referring_doctor_hospital=1,
        diagnosis='Depression and anxiety symptoms',
        doctor_name='Dr. Peter Asiimwe',
        consultant_name=1,
        pharmacy_name=1
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Patient registered successfully!' in response.data
    with app.app_context():
        patient = Patient.query.filter_by(surname='Doe', first_names='John').first()
        assert patient is not None

def test_admit_patient_to_admission_ward(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        p = Patient(name='Jane Doe', age=25, gender='Female', national_id='NID456', status='Registered')
        db.session.add(p)
        db.session.commit()
        patient_id = p.id
        ward_id = Ward.query.filter_by(type='Admission').first().id

    response = client.post(f'/patient/{patient_id}/admit', data=dict(
        ward=ward_id
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Patient admitted' in response.data
    with app.app_context():
        p = Patient.query.get(patient_id)
        assert p.status == 'Admitted'
        assert p.ward_id == ward_id

def test_admit_patient_to_general_ward_fails(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        p = Patient(name='Jane Doe', age=25, gender='Female', national_id='NID789', status='Registered')
        db.session.add(p)
        db.session.commit()
        patient_id = p.id
        ward_id = Ward.query.filter_by(type='General').first().id

    # The form choices only include Admission wards, but we try to POST a General ward ID
    response = client.post(f'/patient/{patient_id}/admit', data=dict(
        ward=ward_id
    ), follow_redirects=True)
    # WTForms validation should fail because ward_id is not in choices
    assert b'Admit Patient' in response.data # Still on admission page
    with app.app_context():
        p = Patient.query.get(patient_id)
        assert p.status == 'Registered'
