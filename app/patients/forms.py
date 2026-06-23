from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, TextAreaField, DateField, DateTimeField
from wtforms.validators import DataRequired, ValidationError, Length, Regexp, Optional
from app.models.models import Patient, MaritalStatus, ReferringDoctorHospital
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
    hospital_id = StringField('Hospital Number', validators=[Optional(), Length(min=1, max=6), Regexp(r'^[0-9]+$', message='Hospital number must contain only digits')])
    surname = StringField('Surname', validators=[DataRequired(), Length(min=2, max=100)])
    first_names = StringField('First Name(s)', validators=[DataRequired(), Length(min=2, max=100)])
    age = IntegerField('Age', validators=[DataRequired()])
    
    sex = SelectField('Sex', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    race = SelectField('Race', choices=[('African', 'African'), ('Caucasian', 'Caucasian'), ('Other', 'Other')], validators=[DataRequired()])
    religion = SelectField('Religion', choices=[('Christianity', 'Christianity'), ('Hinduism', 'Hinduism'), ('Muslim', 'Muslim'), ('Traditional', 'Traditional')], validators=[DataRequired()])
    marital_status = SelectField('Marital Status', coerce=int, validators=[DataRequired()])
    occupation = SelectField('Occupation', choices=[('Employed', 'Employed'), ('Unemployed', 'Unemployed'), ('Self-Employed', 'Self-Employed'), ('Student', 'Student'), ('Other', 'Other')], validators=[DataRequired()])
    
    # Contact Information Section
    residential_address = TextAreaField('Residential Address', validators=[DataRequired(), Length(min=5, max=500)])
    contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=20)])
    
    # Employer Information Section
    employer_name = StringField('Employer Name', validators=[Optional(), Length(max=100)])
    employer_address = TextAreaField('Employer Address', validators=[Optional(), Length(max=500)])
    
    # Next of Kin Information Section
    next_of_kin_name = StringField('Next of Kin Name', validators=[DataRequired(), Length(min=2, max=100)])
    next_of_kin_contact_number = StringField('Next of Kin Contact Number', validators=[DataRequired(), Length(min=10, max=20)])
    next_of_kin_address = TextAreaField('Next of Kin Address', validators=[DataRequired(), Length(min=5, max=500)])
    next_of_kin_relationship = StringField('Relationship to Next of Kin', validators=[DataRequired(), Length(min=2, max=100)])
    
    # Admission Information Section
    admission_datetime = FlexibleDateTimeField('Admission Date & Time', validators=[DataRequired()])
    referring_doctor_hospital = StringField('Referring Doctor/Hospital', validators=[DataRequired(), Length(min=2, max=150)])
    
    # Medical Information Section
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired(), Length(min=10, max=2000)])
    treatment = TextAreaField('Treatment / Current Regimen', validators=[DataRequired(), Length(min=5, max=2000)])
    doctor_name = StringField('Name of Doctor (Who handled patient after admission)', validators=[DataRequired(), Length(min=2, max=100)])
    consultant_name = StringField('Consultant Name', validators=[DataRequired(), Length(min=2, max=100)])
    pharmacy_name = StringField('Pharmacy Name', validators=[DataRequired(), Length(min=2, max=100)])
    
    submit = SubmitField('Register Patient')

    def __init__(self, *args, **kwargs):
        super(PatientRegistrationForm, self).__init__(*args, **kwargs)
        # Populate lookup dropdown choices from database
        self.marital_status.choices = [(m.id, m.name) for m in MaritalStatus.query.all()]

    def validate_hospital_id(self, hospital_id):
        if hospital_id.data:
            hospital_id.data = hospital_id.data.strip().zfill(6)
            existing = Patient.query.filter_by(hospital_id=hospital_id.data).first()
            if existing and not (hasattr(self, 'patient_id') and existing.id == getattr(self, 'patient_id')):
                raise ValidationError('This hospital number already exists. Leave blank to auto-generate or enter a different number.')

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
    referring_doctor_hospital = StringField('Referring Doctor/Hospital', validators=[DataRequired(), Length(min=2, max=150)])
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired(), Length(min=10, max=2000)])
    treatment = TextAreaField('Treatment / Current Regimen', validators=[DataRequired(), Length(min=5, max=2000)])
    doctor_name = StringField('Name of Doctor (Who handled patient after admission)', validators=[DataRequired(), Length(min=2, max=100)])
    consultant_name = StringField('Consultant Name', validators=[DataRequired(), Length(min=2, max=100)])
    pharmacy_name = StringField('Pharmacy Name', validators=[DataRequired(), Length(min=2, max=100)])
    ward = SelectField('Admission Ward', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Readmit Patient')

    def __init__(self, *args, **kwargs):
        super(ReadmitPatientForm, self).__init__(*args, **kwargs)

from flask_wtf.file import FileField, FileAllowed, FileRequired
class ImportForm(FlaskForm):
    file = FileField('Upload CSV or Excel File', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx', 'xls'], 'CSV and Excel files only!')
    ])
    submit = SubmitField('Import Database')
