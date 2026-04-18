import pytest
from app import create_app, db, bcrypt
from app.models.models import User, Role, Ward
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
        roles = ['Admin', 'CMO', 'Sister In Charge', 'Nurse', 'Executive']
        for role_name in roles:
            db.session.add(Role(name=role_name))

        # Seed admin
        admin_role = Role.query.filter_by(name='Admin').first()
        hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin_user = User(name='Admin', email='admin@test.com', password_hash=hashed_pw, role_id=admin_role.id)
        db.session.add(admin_user)

        # Seed nurse
        nurse_role = Role.query.filter_by(name='Nurse').first()
        nurse_user = User(name='Nurse', email='nurse@test.com', password_hash=hashed_pw, role_id=nurse_role.id)
        db.session.add(nurse_user)

        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_login(client):
    response = client.post('/auth/login', data=dict(
        email='admin@test.com',
        password='admin123'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Logout' in response.data

def test_rbac_admin_success(client):
    client.post('/auth/login', data=dict(
        email='admin@test.com',
        password='admin123'
    ), follow_redirects=True)
    response = client.get('/admin_only')
    assert response.status_code == 200
    assert b'Welcome, Admin!' in response.data

def test_rbac_admin_failure(client):
    client.post('/auth/login', data=dict(
        email='nurse@test.com',
        password='admin123'
    ), follow_redirects=True)
    response = client.get('/admin_only')
    assert response.status_code == 403
