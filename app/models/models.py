from datetime import datetime, timezone
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_property

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
    is_permanent_residence = db.Column(db.Boolean, default=False, nullable=False)
    users = db.relationship('User', backref='ward_obj', lazy=True)
    patients = db.relationship('Patient', backref='current_ward', lazy=True)

    @property
    def current_occupancy(self):
        return len(self.patients)

    @property
    def is_full(self):
        if self.is_permanent_residence:
            return False
        if self.capacity is None:
            return False
        return self.current_occupancy >= self.capacity

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=True)

class Race(db.Model):
    __tablename__ = 'races'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class MaritalStatus(db.Model):
    __tablename__ = 'marital_statuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class Occupation(db.Model):
    __tablename__ = 'occupations'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class ReferringDoctorHospital(db.Model):
    __tablename__ = 'referring_doctors_hospitals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # Doctor or Hospital

class Consultant(db.Model):
    __tablename__ = 'consultants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Pharmacy(db.Model):
    __tablename__ = 'pharmacies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    
    # Hospital ID - 6 digit unique identifier
    hospital_id = db.Column(db.String(6), unique=True, nullable=False)
    
    # Personal Information
    surname = db.Column(db.String(100), nullable=False)
    first_names = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String(20), nullable=False)  # Male, Female, Other
    race = db.Column(db.String(50), nullable=False)
    marital_status = db.Column(db.String(50), nullable=False)  # Single, Married, Divorced, Widowed
    occupation = db.Column(db.String(100), nullable=False)
    religion = db.Column(db.String(50), default='Not Applicable')
    
    # Contact Information
    residential_address = db.Column(db.Text, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    
    # Employer Information
    employer_name = db.Column(db.String(100), nullable=True)
    employer_address = db.Column(db.Text, nullable=True)
    
    # Next of Kin Information
    next_of_kin_name = db.Column(db.String(100), nullable=False)
    next_of_kin_contact_number = db.Column(db.String(20), nullable=False)
    next_of_kin_address = db.Column(db.Text, nullable=False)
    next_of_kin_relationship = db.Column(db.String(100), nullable=False)
    
    # Geographical Information (Set to NA by default)
    chief = db.Column(db.String(100), default='Not Applicable')
    village = db.Column(db.String(100), default='Not Applicable')
    tribe = db.Column(db.String(100), default='Not Applicable')
    
    # Admission Information
    admission_datetime = db.Column(db.DateTime, nullable=False)
    referring_doctor_hospital = db.Column(db.String(150), nullable=False)
    
    # Medical Information
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text, nullable=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    consultant_name = db.Column(db.String(100), nullable=False)
    pharmacy_name = db.Column(db.String(100), nullable=False, default='Ingutsheni Pharmacy')
    
    # Discharge/Transfer/Death Information (nullable - filled only when applicable)
    discharge_datetime = db.Column(db.DateTime, nullable=True)
    
    # Status and System Information
    status = db.Column(db.String(50), default='Registered')  # Registered, Admitted, Transferred, Discharged, Deceased
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def name(self):
        return f"{self.surname}, {self.first_names}"

    @name.setter
    def name(self, value):
        if not value:
            self.surname = ""
            self.first_names = ""
            return
        parts = value.split(',', 1)
        if len(parts) == 2:
            # "Surname, Firstname" format
            self.surname = parts[0].strip()
            self.first_names = parts[1].strip()
        else:
            parts = value.split(' ', 1)
            if len(parts) == 2:
                # "Firstname Surname" format
                self.first_names = parts[0].strip()
                self.surname = parts[1].strip()
            else:
                self.first_names = value
                self.surname = value

    @property
    def gender(self):
        return self.sex

    @gender.setter
    def gender(self, value):
        self.sex = value

    @hybrid_property
    def national_id(self):
        return self.hospital_id

    @national_id.setter
    def national_id(self, value):
        self.hospital_id = value

    @national_id.expression
    def national_id(cls):
        return cls.hospital_id

    def __init__(self, **kwargs):
        from datetime import datetime, date
        # Handle custom properties first to avoid conflicts
        name_val = kwargs.pop('name', None)
        gender_val = kwargs.pop('gender', None)
        national_id_val = kwargs.pop('national_id', None)

        if 'date_of_birth' not in kwargs:
            kwargs['date_of_birth'] = date(1990, 1, 1)
        if 'age' not in kwargs:
            kwargs['age'] = 30
        if 'race' not in kwargs:
            kwargs['race'] = 'Other'
        if 'marital_status' not in kwargs:
            kwargs['marital_status'] = 'Single'
        if 'occupation' not in kwargs:
            kwargs['occupation'] = 'Other'
        if 'residential_address' not in kwargs:
            kwargs['residential_address'] = 'Not Provided'
        if 'contact_number' not in kwargs:
            kwargs['contact_number'] = 'Not Provided'
        if 'next_of_kin_name' not in kwargs:
            kwargs['next_of_kin_name'] = 'Not Provided'
        if 'next_of_kin_contact_number' not in kwargs:
            kwargs['next_of_kin_contact_number'] = 'Not Provided'
        if 'next_of_kin_address' not in kwargs:
            kwargs['next_of_kin_address'] = 'Not Provided'
        if 'next_of_kin_relationship' not in kwargs:
            kwargs['next_of_kin_relationship'] = 'Other'
        if 'treatment' not in kwargs:
            kwargs['treatment'] = 'Not Provided'
        if 'admission_datetime' not in kwargs:
            kwargs['admission_datetime'] = datetime.now()
        if 'referring_doctor_hospital' not in kwargs:
            kwargs['referring_doctor_hospital'] = 'Not Applicable'
        if 'diagnosis' not in kwargs:
            kwargs['diagnosis'] = 'Not Provided'
        if 'doctor_name' not in kwargs:
            kwargs['doctor_name'] = 'Not Provided'
        if 'consultant_name' not in kwargs:
            kwargs['consultant_name'] = 'Not Applicable'
        if 'pharmacy_name' not in kwargs:
            kwargs['pharmacy_name'] = 'Not Applicable'
        if 'hospital_id' not in kwargs and not national_id_val:
            import random
            kwargs['hospital_id'] = str(random.randint(25000, 99999)).zfill(6)

        super(Patient, self).__init__(**kwargs)

        # Apply properties via setters
        if name_val is not None:
            self.name = name_val
        if gender_val is not None:
            self.gender = gender_val
        if national_id_val is not None:
            self.national_id = national_id_val

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
    discharge_type = db.Column(db.String(20), default='Discharged')  # 'Discharged' or 'Deceased'
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    ward = db.relationship('Ward', foreign_keys=[ward_id])
    user = db.relationship('User', foreign_keys=[discharged_by])
    notes = db.Column(db.Text)
