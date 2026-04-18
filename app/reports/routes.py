from flask import render_template, url_for, flash, redirect, Blueprint, request
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

    if start_date:
        query = query.filter(Admission.timestamp >= datetime.strptime(start_date, '%Y-%m-%d')) if report_type == 'admissions' else \
                query.filter(Transfer.timestamp >= datetime.strptime(start_date, '%Y-%m-%d')) if report_type == 'transfers' else \
                query.filter(Discharge.timestamp >= datetime.strptime(start_date, '%Y-%m-%d'))

    if end_date:
        query = query.filter(Admission.timestamp <= datetime.strptime(end_date, '%Y-%m-%d')) if report_type == 'admissions' else \
                query.filter(Transfer.timestamp <= datetime.strptime(end_date, '%Y-%m-%d')) if report_type == 'transfers' else \
                query.filter(Discharge.timestamp <= datetime.strptime(end_date, '%Y-%m-%d'))

    results = query.all()

    return render_template('reports/view_reports.html', results=results, report_type=report_type)
