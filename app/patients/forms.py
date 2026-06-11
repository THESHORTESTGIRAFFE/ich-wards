from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, TextAreaField, DateField, DateTimeField
from wtforms.validators import DataRequired, ValidationError, Length, Regexp, Optional
from app.models.models import Patient, Race, MaritalStatus, Occupation, ReferringDoctorHospital, Consultant, Pharmacy
from datetime import datetime as dt_class

class FlexibleDateTimeField(DateTimeField):
    def __init__(self, label=None, validators=None, formats=None, **kwargs):
        self.formats = formats or ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
        super(FlexibleDateTimeField, self).__init__(label, validators, format=self.formats[0], **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist).strip()
            if not date_str:
                self.data = None
                return
            for fmt in self.formats:
                try:
                    self.data = dt_class.strptime(date_str, fmt)
                    return
                except ValueError:
                    continue
            self.data = None
            raise ValueError(self.gettext('Not a valid datetime value.'))

class PatientRegistrationForm(FlaskForm):
    # Personal Information Section
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=100)])
    first_names = StringField('First Name(s)', validators=[DataRequired(), Length(min=2, max=100)])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    
    sex = SelectField('Sex', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    race = SelectField('Race', coerce=int, validators=[DataRequired()])
    marital_status = SelectField('Marital Status', coerce=int, validators=[DataRequired()])
    occupation = SelectField('Occupation', coerce=int, validators=[DataRequired()])
    
    # Contact Information Section
    residential_address = TextAreaField('Residential Address', validators=[DataRequired(), Length(min=5, max=500)])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=20)])
    
    # Employer Information Section
    employer_name = StringField('Employer Name', validators=[Optional(), Length(max=100)])
    employer_address = TextAreaField('Employer Address', validators=[Optional(), Length(max=500)])
    
    # Next of Kin Information Section
    next_of_kin_name = StringField('Next of Kin Name', validators=[DataRequired(), Length(min=2, max=100)])
    next_of_kin_address = TextAreaField('Next of Kin Address', validators=[DataRequired(), Length(min=5, max=500)])
    next_of_kin_relationship = SelectField('Relationship to Patient', 
                                          choices=[('Parent', 'Parent'), ('Sibling', 'Sibling'), ('Spouse', 'Spouse'), 
                                                  ('Child', 'Child'), ('Other', 'Other')], 
                                          validators=[DataRequired()])
    
    # Admission Information Section
    admission_datetime = FlexibleDateTimeField('Admission Date & Time', validators=[DataRequired()])
    referring_doctor_hospital = SelectField('Referring Doctor/Hospital', coerce=int, validators=[DataRequired()])
    
    # Medical Information Section
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired(), Length(min=10, max=2000)])
    doctor_name = StringField('Name of Doctor (Who handled patient after admission)', validators=[DataRequired(), Length(min=2, max=100)])
    consultant_name = SelectField('Consultant Name', coerce=int, validators=[DataRequired()])
    pharmacy_name = SelectField('Pharmacy Name', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Register Patient')

    def __init__(self, *args, **kwargs):
        super(PatientRegistrationForm, self).__init__(*args, **kwargs)
        # Populate dropdown choices from database
        self.race.choices = [(r.id, r.name) for r in Race.query.all()]
        self.marital_status.choices = [(m.id, m.name) for m in MaritalStatus.query.all()]
        self.occupation.choices = [(o.id, o.name) for o in Occupation.query.all()]
        self.referring_doctor_hospital.choices = [(r.id, r.name) for r in ReferringDoctorHospital.query.all()]
        self.consultant_name.choices = [(c.id, c.name) for c in Consultant.query.all()]
        self.pharmacy_name.choices = [(p.id, p.name) for p in Pharmacy.query.all()]

    def validate_date_of_birth(self, date_of_birth):
        from datetime import datetime
        if date_of_birth.data > datetime.now().date():
            raise ValidationError('Date of birth cannot be in the future.')

class AdmissionForm(FlaskForm):
    ward = SelectField('Admission Ward', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Admit Patient')

class DischargeForm(FlaskForm):
    discharge_type = SelectField('Reason for Discharge', 
                                  choices=[('Discharged', 'Discharged — Left Hospital'), ('Deceased', 'Deceased — Patient Passed Away')],
                                  validators=[DataRequired()])
    discharge_datetime = FlexibleDateTimeField('Date & Time', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[DataRequired(), Length(min=5, max=1000)])
    submit = SubmitField('Confirm Discharge')

class ReadmissionForm(FlaskForm):
    hospital_id = StringField('Existing Hospital Number', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Find Patient')

class ReadmitPatientForm(FlaskForm):
    admission_datetime = FlexibleDateTimeField('Admission Date & Time', validators=[DataRequired()])
    referring_doctor_hospital = SelectField('Referring Doctor/Hospital', coerce=int, validators=[DataRequired()])
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired(), Length(min=10, max=2000)])
    doctor_name = StringField('Name of Doctor (Who handled patient after admission)', validators=[DataRequired(), Length(min=2, max=100)])
    consultant_name = SelectField('Consultant Name', coerce=int, validators=[DataRequired()])
    pharmacy_name = SelectField('Pharmacy Name', coerce=int, validators=[DataRequired()])
    ward = SelectField('Admission Ward', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Readmit Patient')

    def __init__(self, *args, **kwargs):
        super(ReadmitPatientForm, self).__init__(*args, **kwargs)
        self.referring_doctor_hospital.choices = [(r.id, r.name) for r in ReferringDoctorHospital.query.all()]
        self.consultant_name.choices = [(c.id, c.name) for c in Consultant.query.all()]
        self.pharmacy_name.choices = [(p.id, p.name) for p in Pharmacy.query.all()]

from flask_wtf.file import FileField, FileAllowed, FileRequired
class ImportForm(FlaskForm):
    file = FileField('Upload CSV or Excel File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx', 'xls'], 'CSV and Excel files only!')
    ])
    submit = SubmitField('Import Database')
