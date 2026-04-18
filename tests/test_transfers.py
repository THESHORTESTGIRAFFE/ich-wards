import pytest
from app import create_app, db, bcrypt
from app.models.models import User, Role, Ward, Patient, Transfer
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
        roles = ['Admin', 'Sister In Charge']
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

def test_transfer_patient(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        admission_ward = Ward.query.filter_by(type='Admission').first()
        general_ward = Ward.query.filter_by(type='General').first()
        p = Patient(name='John Doe', age=30, gender='Male', national_id='NID123', status='Admitted', ward_id=admission_ward.id)
        db.session.add(p)
        db.session.commit()
        patient_id = p.id
        from_ward_id = admission_ward.id
        to_ward_id = general_ward.id

    response = client.post(f'/patient/{patient_id}/transfer', data=dict(
        to_ward=to_ward_id
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Patient transferred successfully!' in response.data
    with app.app_context():
        p = Patient.query.get(patient_id)
        assert p.ward_id == to_ward_id
        transfer = Transfer.query.filter_by(patient_id=patient_id).first()
        assert transfer is not None
        assert transfer.from_ward_id == from_ward_id
        assert transfer.to_ward_id == to_ward_id
