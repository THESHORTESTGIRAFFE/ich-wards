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
        name='John Doe',
        age=30,
        gender='Male',
        national_id='NID123'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Patient registered successfully!' in response.data
    with app.app_context():
        patient = Patient.query.filter_by(national_id='NID123').first()
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
