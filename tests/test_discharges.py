import pytest
from app import create_app, db, bcrypt
from app.models.models import User, Role, Ward, Patient, Discharge
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
        roles = ['Admin']
        for role_name in roles:
            db.session.add(Role(name=role_name))

        # Seed wards
        db.session.add(Ward(name='General Ward', type='General'))
        db.session.add(Ward(name='Discharge Ward', type='Discharge'))

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

def test_discharge_patient_from_discharge_ward(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        discharge_ward = Ward.query.filter_by(type='Discharge').first()
        p = Patient(name='John Doe', age=30, gender='Male', national_id='NID123', status='Admitted', ward_id=discharge_ward.id)
        db.session.add(p)
        db.session.commit()
        patient_id = p.id

    response = client.post(f'/patient/{patient_id}/discharge', data=dict(
        notes='Recovered well.'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Patient discharged successfully!' in response.data
    with app.app_context():
        p = Patient.query.get(patient_id)
        assert p.status == 'Discharged'
        assert p.ward_id is None
        discharge = Discharge.query.filter_by(patient_id=patient_id).first()
        assert discharge is not None
        assert discharge.notes == 'Recovered well.'

def test_discharge_patient_from_general_ward_fails(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        general_ward = Ward.query.filter_by(type='General').first()
        p = Patient(name='Jane Doe', age=25, gender='Female', national_id='NID456', status='Admitted', ward_id=general_ward.id)
        db.session.add(p)
        db.session.commit()
        patient_id = p.id

    response = client.post(f'/patient/{patient_id}/discharge', data=dict(
        notes='Failing discharge.'
    ), follow_redirects=True)
    assert b'Patients can only be discharged via the Discharge Ward' in response.data
    with app.app_context():
        p = Patient.query.get(patient_id)
        assert p.status == 'Admitted'
