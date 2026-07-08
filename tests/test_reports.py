import pytest
from app import create_app, db, bcrypt
from app.models.models import User, Role, Ward, Patient, Admission
from config import Config
from datetime import datetime

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
        db.session.add(Ward(name='Admission Ward', type='Admission'))

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

def test_reports_admissions(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        admin = User.query.filter_by(email='admin@test.com').first()
        ward = Ward.query.filter_by(type='Admission').first()
        p = Patient(name='John Doe', age=30, gender='Male', national_id='NID123', status='Admitted', ward_id=ward.id)
        db.session.add(p)
        db.session.commit()

        adm = Admission(patient_id=p.id, ward_id=ward.id, admitted_by=admin.id, timestamp=datetime.utcnow())
        db.session.add(adm)
        db.session.commit()

    response = client.get('/reports?type=admissions')
    assert response.status_code == 200
    assert b'Doe, John' in response.data
    assert b'Admission Ward' in response.data
    assert b'Admin' in response.data

def test_reports_patients(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        p = Patient(name='Jane Doe', age=25, gender='Female', national_id='NID456', status='Admitted')
        db.session.add(p)
        db.session.commit()

    response = client.get('/reports?type=patients')
    assert response.status_code == 200
    assert b'Doe, Jane' in response.data
    assert b'Date of Admission' in response.data
    assert b'Date of Discharge' in response.data
