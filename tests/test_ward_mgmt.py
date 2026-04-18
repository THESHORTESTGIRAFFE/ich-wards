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
        roles = ['Admin']
        for role_name in roles:
            db.session.add(Role(name=role_name))

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

def test_create_ward(client, app):
    login(client, 'admin@test.com', 'admin123')
    response = client.post('/ward/new', data=dict(
        name='New Ward',
        type='General',
        capacity=10
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Ward created successfully!' in response.data
    with app.app_context():
        ward = Ward.query.filter_by(name='New Ward').first()
        assert ward is not None
        assert ward.type == 'General'
