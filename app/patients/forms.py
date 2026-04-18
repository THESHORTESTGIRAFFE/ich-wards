from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from app.models.models import Patient

class PatientRegistrationForm(FlaskForm):
    name = StringField('Patient Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    national_id = StringField('National ID / Hospital ID', validators=[DataRequired()])
    submit = SubmitField('Register Patient')

    def validate_national_id(self, national_id):
        patient = Patient.query.filter_by(national_id=national_id.data).first()
        if patient:
            raise ValidationError('A patient with this National ID already exists.')

class AdmissionForm(FlaskForm):
    ward = SelectField('Admission Ward', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Admit Patient')

class DischargeForm(FlaskForm):
    notes = TextAreaField('Discharge Notes', validators=[DataRequired()])
    submit = SubmitField('Discharge Patient')
