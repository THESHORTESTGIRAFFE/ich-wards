from app import create_app, db, bcrypt
from app.models.models import Role, Ward, User

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
