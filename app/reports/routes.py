from flask import render_template, url_for, flash, redirect, Blueprint, request, Response
import io
import csv
from flask_login import login_required
from app.models.models import Admission, Transfer, Discharge, Patient, Ward
from app.auth.utils import role_required
from datetime import datetime

reports = Blueprint('reports', __name__)

@reports.route('/reports')
@login_required
@role_required(['Admin', 'CMO', 'Executive'])
def view_reports():
    report_type = request.args.get('type', 'admissions')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = None
    if report_type == 'admissions':
        query = Admission.query
    elif report_type == 'transfers':
        query = Transfer.query
    elif report_type == 'discharges':
        query = Discharge.query
    elif report_type == 'patients':
        query = Patient.query.filter_by(is_deleted=False)
    elif report_type == 'wards':
        query = Ward.query

    if start_date:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))

    results = query.all()

    return render_template('reports/view_reports.html', results=results, report_type=report_type)

@reports.route('/reports/export')
@login_required
@role_required(['Admin', 'CMO', 'Executive'])
def export_reports():
    report_type = request.args.get('type', 'admissions')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = None
    if report_type == 'admissions':
        query = Admission.query
    elif report_type == 'transfers':
        query = Transfer.query
    elif report_type == 'discharges':
        query = Discharge.query
    elif report_type == 'patients':
        query = Patient.query.filter_by(is_deleted=False)
    elif report_type == 'wards':
        query = Ward.query

    if start_date:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date:
        if report_type == 'admissions':
            query = query.filter(Admission.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'transfers':
            query = query.filter(Transfer.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))
        elif report_type == 'discharges':
            query = query.filter(Discharge.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))

    results = query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'admissions':
        writer.writerow(['Patient Name', 'Ward', 'Admitted By', 'Timestamp'])
        for row in results:
            writer.writerow([row.patient.name, row.ward.name, row.user.name, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'transfers':
        writer.writerow(['Patient Name', 'From Ward', 'To Ward', 'Transferred By', 'Timestamp'])
        for row in results:
            writer.writerow([row.patient.name, row.from_ward.name, row.to_ward.name, row.user.name, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'discharges':
        writer.writerow(['Patient Name', 'Ward', 'Discharged By', 'Notes', 'Timestamp'])
        for row in results:
            writer.writerow([row.patient.name, row.ward.name, row.user.name, row.notes, row.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
    elif report_type == 'patients':
        writer.writerow(['Patient Name', 'Age', 'Gender', 'National ID', 'Status', 'Current Ward'])
        for row in results:
            writer.writerow([row.name, row.age, row.gender, row.national_id, row.status, row.current_ward.name if row.current_ward else 'None'])
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
