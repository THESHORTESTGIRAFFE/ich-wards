from datetime import datetime, timezone
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', backref='role_obj', lazy=True)

class Ward(db.Model):
    __tablename__ = 'wards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False) # Admission, General, Discharge
    capacity = db.Column(db.Integer, nullable=True)
    users = db.relationship('User', backref='ward_obj', lazy=True)
    patients = db.relationship('Patient', backref='current_ward', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    national_id = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='Admitted') # Admitted, Transferred, Discharged
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=True)

    admissions = db.relationship('Admission', backref='patient', lazy=True)
    transfers = db.relationship('Transfer', backref='patient', lazy=True)
    discharges = db.relationship('Discharge', backref='patient', lazy=True)

class Admission(db.Model):
    __tablename__ = 'admissions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    admitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    ward = db.relationship('Ward', foreign_keys=[ward_id])
    user = db.relationship('User', foreign_keys=[admitted_by])

class Transfer(db.Model):
    __tablename__ = 'transfers'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    from_ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    to_ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    transferred_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    from_ward = db.relationship('Ward', foreign_keys=[from_ward_id])
    to_ward = db.relationship('Ward', foreign_keys=[to_ward_id])
    user = db.relationship('User', foreign_keys=[transferred_by])

class Discharge(db.Model):
    __tablename__ = 'discharges'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    discharged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    ward = db.relationship('Ward', foreign_keys=[ward_id])
    user = db.relationship('User', foreign_keys=[discharged_by])
    notes = db.Column(db.Text)
