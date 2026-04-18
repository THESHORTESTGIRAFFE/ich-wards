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

def test_create_user(client, app):
    login(client, 'admin@test.com', 'admin123')
    with app.app_context():
        nurse_role_id = Role.query.filter_by(name='Nurse').first().id

    response = client.post('/auth/user/new', data=dict(
        name='New Nurse',
        email='nurse@test.com',
        role=nurse_role_id,
        ward=0,
        password='password123',
        confirm_password='password123'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'User created successfully!' in response.data
    with app.app_context():
        user = User.query.filter_by(email='nurse@test.com').first()
        assert user is not None
        assert user.name == 'New Nurse'

def test_delete_user(client, app):
    login(client, 'admin@test.com', 'admin123')
    # Create a user first
    with app.app_context():
        nurse_role = Role.query.filter_by(name='Nurse').first()
        hashed_pw = bcrypt.generate_password_hash('password123').decode('utf-8')
        user = User(name='Delete Me', email='delete@test.com', password_hash=hashed_pw, role_id=nurse_role.id)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    response = client.post(f'/auth/user/{user_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'User deleted successfully!' in response.data
    with app.app_context():
        user = User.query.get(user_id)
        assert user is None
