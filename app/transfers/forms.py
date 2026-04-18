from flask_wtf import FlaskForm
from wtforms import SubmitField, SelectField
from wtforms.validators import DataRequired

class TransferForm(FlaskForm):
    to_ward = SelectField('Destination Ward', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Transfer Patient')
