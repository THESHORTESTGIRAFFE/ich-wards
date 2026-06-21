from app import create_app, db
from app.models.models import (
    Role, Ward, User, Race, MaritalStatus, Occupation, 
    ReferringDoctorHospital, Consultant, Pharmacy, Patient, 
    Admission, Transfer, Discharge
)

def reset_db():
    app = create_app()
    with app.app_context():
        # Order of deletion matters due to foreign keys
        
        # 1. Clear clinical tables
        db.session.query(Discharge).delete()
        db.session.query(Transfer).delete()
        db.session.query(Admission).delete()
        db.session.query(Patient).delete()
        
        # 2. Clear users except admin
        admin_users = db.session.query(User).filter(User.name == 'Admin').all()
        db.session.query(User).filter(User.name != 'Admin').delete()
        
        # 3. Clear lookup tables
        db.session.query(Consultant).delete()
        db.session.query(Pharmacy).delete()
        db.session.query(ReferringDoctorHospital).delete()
        db.session.query(Occupation).delete()
        db.session.query(MaritalStatus).delete()
        db.session.query(Race).delete()
        
        # 4. Clear structure
        db.session.query(Ward).delete()
        db.session.query(Role).delete()
        
        db.session.commit()
        print("Database reset successfully, administrator(s) preserved.")

if __name__ == '__main__':
    reset_db()
