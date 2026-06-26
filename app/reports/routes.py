from flask import render_template, url_for, flash, redirect, Blueprint, request, Response
import io
import csv
from flask_login import login_required, current_user
from app.models.models import Admission, Transfer, Discharge, Patient, Ward
from app.auth.utils import role_required
from datetime import datetime

reports = Blueprint('reports', __name__)

@reports.route('/reports')
@login_required
@role_required(['Admin', 'CMO', 'Executive', 'Sister In Charge', 'Nurse'])
def view_reports():
    report_type = request.args.get('type', 'admissions')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    role = current_user.role_obj.name
    has_ward_restriction = role in ['Nurse', 'Sister In Charge']

    query = None
    if report_type == 'admissions':
        query = Admission.query
        if has_ward_restriction:
            query = query.filter(Admission.ward_id == current_user.ward_id)
    elif report_type == 'transfers':
        query = Transfer.query
        if has_ward_restriction:
            query = query.filter((Transfer.from_ward_id == current_user.ward_id) | (Transfer.to_ward_id == current_user.ward_id))
    elif report_type == 'discharges':
        query = Discharge.query
        if has_ward_restriction:
            query = query.filter(Discharge.ward_id == current_user.ward_id)
    elif report_type == 'patients':
        query = Patient.query.filter_by(is_deleted=False)
        if has_ward_restriction:
            query = query.filter(Patient.ward_id == current_user.ward_id)
    elif report_type == 'wards':
        query = Ward.query
        if has_ward_restriction:
            query = query.filter(Ward.id == current_user.ward_id)

    if start_date and query:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date and query:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))

    results = query.all() if query else []

    return render_template('reports/view_reports.html', results=results, report_type=report_type)

@reports.route('/reports/export')
@login_required
@role_required(['Admin', 'CMO', 'Executive', 'Sister In Charge', 'Nurse'])
def export_reports():
    report_type = request.args.get('type', 'admissions')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    role = current_user.role_obj.name
    has_ward_restriction = role in ['Nurse', 'Sister In Charge']

    query = None
    if report_type == 'admissions':
        query = Admission.query
        if has_ward_restriction:
            query = query.filter(Admission.ward_id == current_user.ward_id)
    elif report_type == 'transfers':
        query = Transfer.query
        if has_ward_restriction:
            query = query.filter((Transfer.from_ward_id == current_user.ward_id) | (Transfer.to_ward_id == current_user.ward_id))
    elif report_type == 'discharges':
        query = Discharge.query
        if has_ward_restriction:
            query = query.filter(Discharge.ward_id == current_user.ward_id)
    elif report_type == 'patients':
        query = Patient.query.filter_by(is_deleted=False)
        if has_ward_restriction:
            query = query.filter(Patient.ward_id == current_user.ward_id)
    elif report_type == 'wards':
        query = Ward.query
        if has_ward_restriction:
            query = query.filter(Ward.id == current_user.ward_id)

    if start_date and query:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date and query:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))

    results = query.all() if query else []

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'admissions':
        writer.writerow(['Patient Name', 'Age', 'Diagnosis', 'Type', 'Ward', 'Timestamp'])
        for row in results:
            admission_type = 'Readmission' if len(row.patient.admissions) > 1 else 'New'
            writer.writerow([row.patient.name, row.patient.age, row.patient.diagnosis or '', admission_type, row.ward.name, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'transfers':
        writer.writerow(['Patient Name', 'From Ward', 'To Ward', 'Transferred By', 'Timestamp'])
        for row in results:
            writer.writerow([row.patient.name, row.from_ward.name, row.to_ward.name, row.user.name, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'discharges':
        writer.writerow(['Patient Name', 'Ward', 'Discharged By', 'Notes', 'Timestamp'])
        for row in results:
            writer.writerow([row.patient.name, row.ward.name, row.user.name, row.notes, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'patients':
        writer.writerow(['Patient Name', 'Age', 'Sex', 'Hospital ID', 'Status', 'Current Ward', 'Diagnosis', 'Treatment', 'Admission Date', 'Discharge Date'])
        for row in results:
            writer.writerow([row.name, row.age, row.sex, row.hospital_id, row.status, row.current_ward.name if row.current_ward else 'None', row.diagnosis or '', row.treatment or '', row.admission_datetime.strftime('%Y-%m-%d %H:%M:%S') if row.admission_datetime else 'N/A', row.discharge_datetime.strftime('%Y-%m-%d %H:%M:%S') if row.discharge_datetime else 'N/A'])
    elif report_type == 'wards':
        writer.writerow(['Ward Name', 'Type', 'Capacity', 'Current Occupancy', 'Is Full'])
        for row in results:
            writer.writerow([row.name, row.type, row.capacity if row.capacity else 'N/A', row.current_occupancy, 'Yes' if row.is_full else 'No'])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={report_type}_report_{datetime.now().strftime('%Y%m%d')}.csv"}
    )
