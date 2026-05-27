from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError
from app.models.models import Ward

class WardForm(FlaskForm):
    name = StringField('Ward Name', validators=[DataRequired()])
    type = SelectField('Ward Type', choices=[('Admission', 'Admission'), ('General', 'General'), ('Discharge', 'Discharge')], validators=[DataRequired()])
    capacity = IntegerField('Capacity (Optional)')
    submit = SubmitField('Submit')

    def __init__(self, original_name=None, *args, **kwargs):
        super(WardForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        ward = Ward.query.filter_by(name=name.data).first()
        if ward and name.data != self.original_name:
            raise ValidationError('A ward with this name already exists.')
