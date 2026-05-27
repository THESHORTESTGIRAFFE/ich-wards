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

    from datetime import timedelta
    labels = []
    admissions_data = []
    discharges_data = []
    
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime('%b %d'))
        admissions_count = Admission.query.filter(db.func.date(Admission.timestamp) == d).count()
        discharges_count = Discharge.query.filter(db.func.date(Discharge.timestamp) == d).count()
        admissions_data.append(admissions_count)
        discharges_data.append(discharges_count)
        
    ward_labels = [w.name for w in wards]
    ward_occupancy_data = [w.current_occupancy for w in wards]
    
    status_counts = db.session.query(Patient.status, db.func.count(Patient.id)).filter_by(is_deleted=False).group_by(Patient.status).all()
    status_labels = [s[0] for s in status_counts]
    status_data = [s[1] for s in status_counts]

    return render_template('main/index.html',
                           total_patients=total_patients,
                           wards=wards,
                           admissions_today=admissions_today,
                           transfers_today=transfers_today,
                           discharges_today=discharges_today,
                           chart_labels=labels,
                           chart_admissions=admissions_data,
                           chart_discharges=discharges_data,
                           ward_labels=ward_labels,
                           ward_occupancy_data=ward_occupancy_data,
                           status_labels=status_labels,
                           status_data=status_data)

@main.route('/admin_only')
@login_required
@role_required(['Admin'])
def admin_only():
    return "Welcome, Admin!"

@main.route('/test')
def test():
    return jsonify({"status": "Success", "message": "App is running"})
