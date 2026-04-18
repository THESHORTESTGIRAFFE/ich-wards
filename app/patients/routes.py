from flask import render_template, url_for, flash, redirect, Blueprint, request
from flask_login import login_required, current_user
from app import db
from app.models.models import Patient, Ward, Admission, Discharge
from app.patients.forms import PatientRegistrationForm, AdmissionForm, DischargeForm
from app.auth.utils import role_required
from datetime import datetime

patients = Blueprint('patients', __name__)

@patients.route('/patients')
@login_required
def list_patients():
    all_patients = Patient.query.all()
    return render_template('patients/list_patients.html', patients=all_patients)

@patients.route('/patient/register', methods=['GET', 'POST'])
@login_required
def register_patient():
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        patient = Patient(
            name=form.name.data,
            age=form.age.data,
            gender=form.gender.data,
            national_id=form.national_id.data,
            status='Registered'
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient registered successfully!', 'success')
        return redirect(url_for('patients.list_patients'))
    return render_template('patients/register.html', title='Register Patient', form=form)

@patients.route('/patient/<int:patient_id>/admit', methods=['GET', 'POST'])
@login_required
def admit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.status == 'Admitted':
        flash('Patient is already admitted.', 'warning')
        return redirect(url_for('patients.list_patients'))

    # RBAC: Only Nurses and Sister In Charge of Admission Wards, or Admin/CMO can admit
    if current_user.role_obj.name in ['Nurse', 'Sister In Charge']:
        if not current_user.ward_id or current_user.ward_obj.type != 'Admission':
            flash('You are not assigned to an Admission Ward and cannot perform admissions.', 'danger')
            return redirect(url_for('patients.list_patients'))
        admission_wards = [current_user.ward_obj]
    elif current_user.role_obj.name in ['Admin', 'CMO']:
        admission_wards = Ward.query.filter_by(type='Admission').all()
    else:
        flash('You do not have permission to admit patients.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = AdmissionForm()
    form.ward.choices = [(w.id, w.name) for w in admission_wards]

    if form.validate_on_submit():
        ward_id = form.ward.data
        ward = Ward.query.get(ward_id)

        # Enforce rule: Patients can only be admitted via Admission Wards
        if ward.type != 'Admission':
            flash('Patients can only be admitted via Admission Wards.', 'danger')
            return redirect(url_for('patients.admit_patient', patient_id=patient_id))

        patient.status = 'Admitted'
        patient.ward_id = ward_id
        admission = Admission(patient_id=patient.id, ward_id=ward_id, admitted_by=current_user.id)
        db.session.add(admission)
        db.session.commit()
        flash(f'Patient admitted to {ward.name} successfully!', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('patients/admit.html', title='Admit Patient', form=form, patient=patient)

@patients.route('/patient/<int:patient_id>/discharge', methods=['GET', 'POST'])
@login_required
def discharge_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.status != 'Admitted':
        flash('Only admitted patients can be discharged.', 'warning')
        return redirect(url_for('patients.list_patients'))

    ward = Ward.query.get(patient.ward_id)
    # Enforce rule: Patients can only be discharged via the Discharge Ward
    if ward.type != 'Discharge':
        flash('Patients can only be discharged via the Discharge Ward. Please transfer them to the Discharge Ward first.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = DischargeForm()
    if form.validate_on_submit():
        patient.status = 'Discharged'
        patient.ward_id = None
        discharge = Discharge(
            patient_id=patient.id,
            ward_id=ward.id,
            discharged_by=current_user.id,
            notes=form.notes.data
        )
        db.session.add(discharge)
        db.session.commit()
        flash('Patient discharged successfully!', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('patients/discharge.html', title='Discharge Patient', form=form, patient=patient)
