from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.auth.utils import role_required
from app.models.models import Patient, Ward, Admission, Transfer, Discharge
from datetime import datetime, date

main = Blueprint('main', __name__)

@main.route('/')
def index():
    total_patients = Patient.query.filter(Patient.status == 'Admitted').count()
    wards = Ward.query.all()

    today = date.today()
    from app import db
    admissions_today = Admission.query.filter(db.func.date(Admission.timestamp) == today).count()
    transfers_today = Transfer.query.filter(db.func.date(Transfer.timestamp) == today).count()
    discharges_today = Discharge.query.filter(db.func.date(Discharge.timestamp) == today).count()

    return render_template('main/index.html',
                           total_patients=total_patients,
                           wards=wards,
                           admissions_today=admissions_today,
                           transfers_today=transfers_today,
                           discharges_today=discharges_today)

@main.route('/admin_only')
@login_required
@role_required(['Admin'])
def admin_only():
    return "Welcome, Admin!"

@main.route('/test')
def test():
    return jsonify({"status": "Success", "message": "App is running"})
