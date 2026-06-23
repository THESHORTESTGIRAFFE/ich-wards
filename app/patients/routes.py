from flask import render_template, url_for, flash, redirect, Blueprint, request, current_app, send_file
from flask_login import login_required, current_user
import sqlite3
import io
from app import db
from app.models.models import (Patient, Ward, Admission, Discharge, Transfer, Race, MaritalStatus, 
                              Occupation, ReferringDoctorHospital, Consultant, Pharmacy)
from app.patients.forms import PatientRegistrationForm, AdmissionForm, DischargeForm, ImportForm, ReadmissionForm, ReadmitPatientForm
from app.auth.utils import role_required
import os
import pandas as pd
import re
from datetime import datetime, timezone

patients = Blueprint('patients', __name__)

def generate_hospital_id():
    """Generate a unique 6-digit hospital ID starting from 025000"""
    last_patient = Patient.query.order_by(Patient.id.desc()).first()
    if last_patient and last_patient.hospital_id:
        try:
            last_num = int(last_patient.hospital_id)
            next_num = last_num + 1
        except ValueError:
            next_num = 25000
    else:
        next_num = 25000
    return str(next_num).zfill(6)

@patients.route('/database/backup')
@login_required
@role_required(['Admin', 'CMO'])
def backup_database():
    try:
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        
        conn = sqlite3.connect(db_path)
        sql_dump = io.StringIO()
        for line in conn.iterdump():
            sql_dump.write(line + '\n')
        conn.close()
        
        mem = io.BytesIO()
        mem.write(sql_dump.getvalue().encode('utf-8'))
        mem.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"hospital_backup_{timestamp}.sql"
        
        return send_file(
            mem,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'danger')
        return redirect(url_for('patients.list_patients'))

@patients.route('/patients')
@login_required
def list_patients():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    search = request.args.get('search', '')
    status = request.args.get('status', '')

    query = Patient.query.filter_by(is_deleted=False)

    # Nurses & Sister In Charge only see patients in their own ward
    role = current_user.role_obj.name
    if role in ['Nurse', 'Sister In Charge']:
        query = query.filter(Patient.ward_id == current_user.ward_id)

    if search:
        query = query.filter(
            (Patient.surname.ilike(f'%{search}%')) |
            (Patient.first_names.ilike(f'%{search}%')) |
            (Patient.hospital_id.ilike(f'%{search}%'))
        )

    if status:
        query = query.filter(Patient.status == status)

    if sort == 'hospital_id':
        if order == 'desc':
            query = query.order_by(Patient.hospital_id.desc())
        else:
            query = query.order_by(Patient.hospital_id.asc())
    else:
        if order == 'desc':
            query = query.order_by(Patient.surname.desc(), Patient.first_names.desc())
        else:
            query = query.order_by(Patient.surname.asc(), Patient.first_names.asc())

    pagination = query.paginate(page=page, per_page=15, error_out=False)
    all_patients = pagination.items

    return render_template('patients/list_patients.html', patients=all_patients, pagination=pagination, search=search, status=status, sort=sort, order=order)

@patients.route('/patient/<int:patient_id>')
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    # Access control: Nurses and Sisters in Charge can only view patients in their own ward
    role = current_user.role_obj.name
    if role in ['Nurse', 'Sister In Charge']:
        if patient.ward_id != current_user.ward_id or current_user.ward_id is None:
            flash('You do not have permission to view patients in other wards.', 'danger')
            return redirect(url_for('patients.list_patients'))
    return render_template('patients/detail.html', patient=patient)

@patients.route('/patient/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    
    # Access control: Nurses and Sisters in Charge can only edit patients in their own ward
    role = current_user.role_obj.name
    if role in ['Nurse', 'Sister In Charge']:
        if patient.ward_id != current_user.ward_id or current_user.ward_id is None:
            flash('You do not have permission to edit patients in other wards.', 'danger')
            return redirect(url_for('patients.list_patients'))

    form = PatientRegistrationForm(obj=patient)
    form.patient_id = patient.id
    if request.method == 'GET':
        form.hospital_id.data = patient.hospital_id
        form.race.data = patient.race
        form.religion.data = patient.religion or 'Christianity'
        form.marital_status.data = MaritalStatus.query.filter_by(name=patient.marital_status).first().id if patient.marital_status else None
        form.occupation.data = patient.occupation
        form.next_of_kin_contact_number.data = patient.next_of_kin_contact_number
        form.treatment.data = patient.treatment
    if form.validate_on_submit():
        try:
            hospital_id = form.hospital_id.data.strip().zfill(6) if form.hospital_id.data else patient.hospital_id
            if hospital_id != patient.hospital_id and Patient.query.filter_by(hospital_id=hospital_id).first():
                flash(f'Hospital number {hospital_id} is already in use. Please choose a different number.', 'danger')
                return render_template('patients/register.html', title='Edit Patient', form=form, edit=True, patient=patient)

            patient.hospital_id = hospital_id
            patient.surname = form.surname.data
            patient.first_names = form.first_names.data
            patient.age = form.age.data
            patient.sex = form.sex.data
            patient.race = form.race.data
            patient.religion = form.religion.data
            patient.marital_status = MaritalStatus.query.get(form.marital_status.data).name
            patient.occupation = form.occupation.data
            patient.residential_address = form.residential_address.data
            patient.contact_number = form.contact_number.data
            patient.employer_name = form.employer_name.data or ''
            patient.employer_address = form.employer_address.data or ''
            patient.next_of_kin_name = form.next_of_kin_name.data
            patient.next_of_kin_contact_number = form.next_of_kin_contact_number.data
            patient.next_of_kin_address = form.next_of_kin_address.data
            patient.next_of_kin_relationship = form.next_of_kin_relationship.data
            patient.admission_datetime = form.admission_datetime.data
            patient.referring_doctor_hospital = form.referring_doctor_hospital.data
            patient.diagnosis = form.diagnosis.data
            patient.treatment = form.treatment.data
            patient.doctor_name = form.doctor_name.data
            patient.consultant_name = form.consultant_name.data
            patient.pharmacy_name = form.pharmacy_name.data
            db.session.commit()
            flash('Patient details updated successfully.', 'success')
            return redirect(url_for('patients.view_patient', patient_id=patient.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating patient: {str(e)}', 'danger')
    return render_template('patients/register.html', title='Edit Patient', form=form, edit=True, patient=patient)

@patients.route('/patient/register', methods=['GET', 'POST'])
@login_required
def register_patient():
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            hospital_id = form.hospital_id.data.strip().zfill(6) if form.hospital_id.data else generate_hospital_id()

            if Patient.query.filter_by(hospital_id=hospital_id).first():
                flash(f'Hospital number {hospital_id} is already in use. Please choose a different number.', 'danger')
                return render_template('patients/register.html', title='Register Patient', form=form)

            # Create new patient with all fields
            patient = Patient(
                hospital_id=hospital_id,
                surname=form.surname.data,
                first_names=form.first_names.data,
                age=form.age.data,
                sex=form.sex.data,
                race=form.race.data,
                marital_status=MaritalStatus.query.get(form.marital_status.data).name,
                occupation=form.occupation.data,
                religion=form.religion.data,
                residential_address=form.residential_address.data,
                contact_number=form.contact_number.data,
                employer_name=form.employer_name.data or '',
                employer_address=form.employer_address.data or '',
                next_of_kin_name=form.next_of_kin_name.data,
                next_of_kin_contact_number=form.next_of_kin_contact_number.data,
                next_of_kin_address=form.next_of_kin_address.data,
                next_of_kin_relationship=form.next_of_kin_relationship.data,
                admission_datetime=form.admission_datetime.data,
                referring_doctor_hospital=form.referring_doctor_hospital.data,
                diagnosis=form.diagnosis.data,
                treatment=form.treatment.data,
                doctor_name=form.doctor_name.data,
                consultant_name=form.consultant_name.data,
                pharmacy_name=form.pharmacy_name.data,
                status='Registered'
            )
            db.session.add(patient)
            db.session.commit()
            flash(f'Patient registered successfully! Hospital ID: {hospital_id}', 'success')
            return redirect(url_for('patients.list_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering patient: {str(e)}', 'danger')
    return render_template('patients/register.html', title='Register Patient', form=form)
@patients.route('/patient/<int:patient_id>/admit', methods=['GET', 'POST'])
@login_required
def admit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.status == 'Admitted':
        flash('Patient is already admitted.', 'warning')
        return redirect(url_for('patients.list_patients'))

    # RBAC: Only Sister In Charge of Admission Wards, or Admin/CMO can admit
    if current_user.role_obj.name == 'Sister In Charge':
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

        if ward.is_full:
            flash(f'Ward {ward.name} is currently at full capacity ({ward.capacity}). Please transfer or discharge a patient before admitting more.', 'danger')
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
    if patient.status not in ['Admitted', 'Transferred']:
        flash('Only admitted patients can be discharged.', 'warning')
        return redirect(url_for('patients.list_patients'))

    # RBAC: Sister In Charge and above can discharge
    role = current_user.role_obj.name
    if role not in ['Admin', 'CMO', 'Sister In Charge']:
        flash('You do not have permission to discharge patients.', 'danger')
        return redirect(url_for('patients.list_patients'))

    ward = Ward.query.get(patient.ward_id)
    form = DischargeForm()
    if form.validate_on_submit():
        discharge_type = form.discharge_type.data  # 'Discharged' or 'Deceased'
        patient.status = discharge_type  # Sets to 'Discharged' or 'Deceased'
        patient.discharge_datetime = form.discharge_datetime.data
        patient.ward_id = None
        discharge = Discharge(
            patient_id=patient.id,
            ward_id=ward.id,
            discharged_by=current_user.id,
            discharge_type=discharge_type,
            notes=form.notes.data
        )
        db.session.add(discharge)
        db.session.commit()
        label = 'marked as deceased' if discharge_type == 'Deceased' else 'discharged'
        flash(f'Patient {label} successfully!', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('patients/discharge.html', title='Discharge / Deceased', form=form, patient=patient, ward=ward)

@patients.route('/patient/<int:patient_id>/history')
@login_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    # Access control: Nurses and Sisters in Charge can only view history of patients in their own ward
    role = current_user.role_obj.name
    if role in ['Nurse', 'Sister In Charge']:
        if patient.ward_id != current_user.ward_id or current_user.ward_id is None:
            flash('You do not have permission to view history of patients in other wards.', 'danger')
            return redirect(url_for('patients.list_patients'))
    admissions = Admission.query.filter_by(patient_id=patient_id).order_by(Admission.timestamp.asc()).all()
    transfers = Transfer.query.filter_by(patient_id=patient_id).order_by(Transfer.timestamp.desc()).all()
    discharges = Discharge.query.filter_by(patient_id=patient_id).order_by(Discharge.timestamp.asc()).all()

    # --- Statistics: Average Length of Stay ---
    stays = []
    for adm in admissions:
        # Match each admission to the next discharge after it
        matching_discharge = next(
            (d for d in discharges if d.timestamp >= adm.timestamp), None
        )
        if matching_discharge:
            adm_ts = adm.timestamp.replace(tzinfo=None)
            dis_ts = matching_discharge.timestamp.replace(tzinfo=None)
            los = round((dis_ts - adm_ts).total_seconds() / 86400.0, 1)
            stays.append(max(los, 0.1))  # Ensure at least 0.1 days to avoid 0 for same-day stays

    total_admissions = len(admissions)
    total_transfers = len(transfers)
    total_discharges = len(discharges)
    avg_los = round(sum(stays) / len(stays), 1) if stays else None
    current_los = None
    if patient.status == 'Admitted' and admissions:
        last_adm = admissions[-1]
        adm_ts = last_adm.timestamp.replace(tzinfo=None)
        current_los = round((datetime.now(timezone.utc).replace(tzinfo=None) - adm_ts).total_seconds() / 86400.0, 1)
        current_los = max(current_los, 0.1)

    # Combine and sort all events by timestamp for timeline
    events = []
    for a in admissions:
        events.append({'type': 'Admission', 'timestamp': a.timestamp, 'ward': a.ward.name, 'by': a.user.name})
    for t in transfers:
        events.append({'type': 'Transfer', 'timestamp': t.timestamp, 'from_ward': t.from_ward.name, 'to_ward': t.to_ward.name, 'by': t.user.name})
    for d in discharges:
        events.append({'type': d.discharge_type or 'Discharge', 'timestamp': d.timestamp, 'ward': d.ward.name, 'by': d.user.name, 'notes': d.notes})

    events.sort(key=lambda x: x['timestamp'], reverse=True)

    stats = {
        'total_admissions': total_admissions,
        'total_transfers': total_transfers,
        'total_discharges': total_discharges,
        'avg_los': avg_los,
        'current_los': current_los,
    }

    return render_template('patients/history.html', patient=patient, events=events, stats=stats)

@patients.route('/patient/readmit', methods=['GET', 'POST'])
@login_required
def readmit_patient():
    """Look up a previously discharged patient by hospital ID for re-admission."""
    role = current_user.role_obj.name
    if role not in ['Admin', 'CMO', 'Sister In Charge']:
        flash('You do not have permission to readmit patients.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = ReadmissionForm()
    if form.validate_on_submit():
        hosp_id = form.hospital_id.data.strip().zfill(6)
        found_patient = Patient.query.filter_by(hospital_id=hosp_id, is_deleted=False).first()
        if not found_patient:
            flash(f'No patient found with hospital number {hosp_id}.', 'danger')
        elif found_patient.status in ['Admitted', 'Transferred']:
            flash(f'Patient {found_patient.surname} is already admitted.', 'warning')
        else:
            return redirect(url_for('patients.readmit_patient_details', patient_id=found_patient.id))

    return render_template('patients/readmit.html', title='Find Patient for Readmission', form=form)

@patients.route('/patient/<int:patient_id>/readmit_details', methods=['GET', 'POST'])
@login_required
def readmit_patient_details(patient_id):
    """Update clinical details and admit a previously discharged patient."""
    role = current_user.role_obj.name
    if role not in ['Admin', 'CMO', 'Sister In Charge']:
        flash('You do not have permission to readmit patients.', 'danger')
        return redirect(url_for('patients.list_patients'))

    patient = Patient.query.get_or_404(patient_id)
    if patient.status in ['Admitted', 'Transferred']:
        flash('Patient is already admitted.', 'warning')
        return redirect(url_for('patients.list_patients'))

    # RBAC: Only Sister In Charge of Admission Wards, or Admin/CMO can admit
    if current_user.role_obj.name == 'Sister In Charge':
        if not current_user.ward_id or current_user.ward_obj.type != 'Admission':
            flash('You are not assigned to an Admission Ward and cannot perform admissions.', 'danger')
            return redirect(url_for('patients.list_patients'))
        admission_wards = [current_user.ward_obj]
    elif current_user.role_obj.name in ['Admin', 'CMO']:
        admission_wards = Ward.query.filter_by(type='Admission').all()
    else:
        flash('You do not have permission to admit patients.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = ReadmitPatientForm()
    form.ward.choices = [(w.id, w.name) for w in admission_wards]

    if form.validate_on_submit():
        ward_id = form.ward.data
        ward = Ward.query.get(ward_id)

        if ward.type != 'Admission':
            flash('Patients can only be admitted via Admission Wards.', 'danger')
            return redirect(url_for('patients.readmit_patient_details', patient_id=patient.id))

        if ward.is_full:
            flash(f'Ward {ward.name} is currently at full capacity ({ward.capacity}). Please transfer or discharge a patient before admitting more.', 'danger')
            return redirect(url_for('patients.readmit_patient_details', patient_id=patient.id))

        try:
            # Update Patient details
            patient.status = 'Admitted'
            patient.ward_id = ward_id
            patient.discharge_datetime = None
            patient.admission_datetime = form.admission_datetime.data
            patient.referring_doctor_hospital = form.referring_doctor_hospital.data
            patient.diagnosis = form.diagnosis.data
            patient.treatment = form.treatment.data
            patient.doctor_name = form.doctor_name.data
            patient.consultant_name = form.consultant_name.data
            patient.pharmacy_name = form.pharmacy_name.data

            # Log Admission
            admission = Admission(patient_id=patient.id, ward_id=ward_id, admitted_by=current_user.id)
            db.session.add(admission)
            db.session.commit()
            flash(f'Patient {patient.name} has been readmitted to {ward.name} successfully!', 'success')
            return redirect(url_for('patients.list_patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error during readmission: {str(e)}', 'danger')

    elif request.method == 'GET':
        form.admission_datetime.data = datetime.now()
        form.diagnosis.data = patient.diagnosis
        form.treatment.data = patient.treatment
        form.doctor_name.data = patient.doctor_name
        
        form.referring_doctor_hospital.data = patient.referring_doctor_hospital
        form.consultant_name.data = patient.consultant_name
        form.pharmacy_name.data = patient.pharmacy_name

    return render_template('patients/readmit_details.html', title='Readmit Patient', form=form, patient=patient)

@patients.route('/patient/<int:patient_id>/delete', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.status == 'Admitted':
        flash('Cannot delete a patient who is currently admitted. Please discharge them first.', 'danger')
        return redirect(url_for('patients.list_patients'))

    patient.is_deleted = True
    db.session.commit()
    flash(f'Patient {patient.surname} has been removed from the active system.', 'success')
    return redirect(url_for('patients.list_patients'))

@patients.route('/patients/import', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'CMO'])
def import_database():
    form = ImportForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = file.filename
        
        # We can read the file using pandas
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            # Normalize column names to lowercase for case-insensitive matching
            # Normalize column names: lowercase, strip and remove non-alphanumeric
            # This helps match headers like "HOSPITAL NUMBER", "NEXT OF KIN AND NAME", etc.
            orig_cols = list(df.columns)
            normalized = []
            for c in orig_cols:
                if isinstance(c, str):
                    norm = re.sub(r'[^0-9a-z]', '', c.strip().lower())
                else:
                    norm = str(c)
                normalized.append(norm)
            df.columns = normalized
                
            # Map to Patient models
            success_count = 0
            skipped_count = 0
            error_count = 0
            for index, row in df.iterrows():
                try:
                    def get_val(col_names, default='Not Provided'):
                        """Robust column lookup using normalized column names.
                        `col_names` may contain variants like 'hospital number' or 'hospital_id'.
                        Returns `default` if not found or blank.
                        """
                        for c in col_names:
                            if not isinstance(c, str):
                                continue
                            cand = re.sub(r'[^0-9a-z]', '', c.strip().lower())
                            if cand in df.columns:
                                val = row[cand]
                                if pd.notna(val) and str(val).strip() and str(val).strip() != '-':
                                    return str(val).strip()
                        return default

                    hospital_id = get_val(['hospital number', 'hospital_id', 'hospital name', 'hospital id'], None)
                    
                    if not hospital_id:
                        skipped_count += 1
                        continue

                    # Pad hospital_id to 6 digits
                    hospital_id = str(hospital_id).strip().zfill(6)
                        
                    # Check if already exists
                    if Patient.query.filter_by(hospital_id=hospital_id).first():
                        skipped_count += 1
                        continue

                    surname = get_val(['surname'], 'Not Provided')
                    first_names = get_val(['name', 'name(s)', 'first_names', 'first name'], 'Not Provided')
                    
                    # Parse age
                    age_raw = get_val(['age'], None)
                    age = 0
                    if age_raw:
                        try:
                            age = int(float(age_raw))
                        except (ValueError, TypeError):
                            age = 0
                    
                    # Parse date of birth - handle various formats (as fallback if age is 0)
                    dob_str = get_val(['date of birth', 'dob'], None)
                    if age == 0 and dob_str:
                        try:
                            dob = pd.to_datetime(dob_str, dayfirst=True, errors='coerce')
                            if pd.notna(dob):
                                dob = dob.date()
                                age = datetime.now().year - dob.year
                            else:
                                # Try parsing just a year
                                try:
                                    year = int(float(dob_str))
                                    if 1900 <= year <= 2030:
                                        from datetime import date
                                        age = datetime.now().year - year
                                    else:
                                        age = 0
                                except (ValueError, TypeError):
                                    age = 0
                        except Exception:
                            age = 0
                    
                    sex_raw = get_val(['sex', 'gender'], 'Other')
                    # Map M/F to Male/Female
                    sex_map = {'m': 'Male', 'f': 'Female', 'male': 'Male', 'female': 'Female'}
                    sex = sex_map.get(sex_raw.lower(), sex_raw if sex_raw != 'Not Provided' else 'Other')

                    race_raw = get_val(['race'], 'Other')
                    # Map common codes
                    race_map = {'a': 'African', 'c': 'Caucasian', 'asian': 'Asian', 'african': 'African', 'caucasian': 'Caucasian'}
                    race = race_map.get(race_raw.lower(), race_raw if race_raw != 'Not Provided' else 'Other')

                    marital_status = get_val(['marital status'], 'Not Applicable')
                    occupation_raw = get_val(['occupation'], 'Not Applicable')
                    # Map common abbreviations
                    occ_map = {'u/e': 'Unemployed', 'nil': 'Unemployed', 'n/a': 'Not Applicable'}
                    occupation = occ_map.get(occupation_raw.lower(), occupation_raw)

                    residential_address = get_val(['address', 'residential address'], 'Not Provided')
                    contact_number = get_val(['contact number', 'phone'], 'Not Provided')
                    
                    next_of_kin_name = get_val(['next of kin and name', 'next of kin name'], 'Not Provided')
                    next_of_kin_contact_number = get_val(['next of kin contact number', 'next of kin phone', 'next of kin telephone', 'nok phone', 'phone of next of kin', 'next of kin contact'], 'Not Provided')
                    next_of_kin_address = get_val(['next of kin address'], 'Not Provided')
                    next_of_kin_relationship = get_val(['next of kin relationship', 'relationship to next of kin', 'next of kin relation', 'relationship'], 'Not Provided')
                    # Extract phone from next_of_kin_address if present
                    
                    religion = get_val(['religion'], 'Not Applicable')
                    religion_map = {'unknown': 'Not Applicable'}
                    religion = religion_map.get(religion.lower(), religion)

                    treatment = get_val(['treatment', 'current regimen', 'regimen', 'treatment plan'], 'Not Provided')

                    chief = get_val(['chief'], 'Not Applicable')
                    village = get_val(['village'], 'Not Applicable')
                    tribe = get_val(['tribe'], 'Not Applicable')

                    referring = get_val(['name of doctor/referring hospital', 'referring hospital', 'referring doctor hospital'], 'Not Applicable')
                    pharmacy = get_val(['name of pharmacy', 'pharmacy'], 'Not Applicable')
                    consultant = get_val(['name of consultant', 'consultant'], 'Not Applicable')
                    handling_doctor = get_val(['name of doctor', 'doctor', 'doctor_name'], 'Not Applicable')
                    diagnosis = get_val(['diagnosis', 'diagnosis of patient'], 'Not Provided')
                    
                    # Parse admission date
                    admission_dt_str = get_val(['date of admission', 'admission date', 'admission date and time'], None)
                    admission_dt = None
                    if admission_dt_str:
                        try:
                            admission_dt = pd.to_datetime(admission_dt_str, dayfirst=True, errors='coerce')
                            if pd.notna(admission_dt):
                                admission_dt = admission_dt.to_pydatetime()
                            else:
                                admission_dt = None
                        except Exception:
                            admission_dt = None
                    if admission_dt is None:
                        admission_dt = datetime.now()

                    # Parse discharge date
                    discharge_dt_str = get_val(['date of discharge', 'discharge date', 'date and time of discharge, transfer, or death'], None)
                    discharge_dt = None
                    if discharge_dt_str:
                        # Remove annotations like "(ABSENTIA)" before parsing
                        clean_dt = re.sub(r'\(.*?\)', '', discharge_dt_str).strip()
                        if clean_dt:
                            try:
                                discharge_dt = pd.to_datetime(clean_dt, dayfirst=True, errors='coerce')
                                if pd.notna(discharge_dt):
                                    discharge_dt = discharge_dt.to_pydatetime()
                                else:
                                    discharge_dt = None
                            except Exception:
                                discharge_dt = None

                    # Auto-add to lookup tables if they don't exist
                    if not Race.query.filter_by(name=race).first():
                        db.session.add(Race(name=race))
                        db.session.flush()
                    if not MaritalStatus.query.filter_by(name=marital_status).first():
                        db.session.add(MaritalStatus(name=marital_status))
                        db.session.flush()
                    if not Occupation.query.filter_by(name=occupation).first():
                        db.session.add(Occupation(name=occupation))
                        db.session.flush()
                    if not ReferringDoctorHospital.query.filter_by(name=referring).first():
                        db.session.add(ReferringDoctorHospital(name=referring, type='Hospital'))
                        db.session.flush()
                    if not Consultant.query.filter_by(name=consultant).first():
                        db.session.add(Consultant(name=consultant))
                        db.session.flush()
                    if not Pharmacy.query.filter_by(name=pharmacy).first():
                        db.session.add(Pharmacy(name=pharmacy))
                        db.session.flush()

                    patient = Patient(
                        hospital_id=hospital_id,
                        surname=surname,
                        first_names=first_names,
                        age=age,
                        sex=sex,
                        race=race,
                        marital_status=marital_status,
                        occupation=occupation,
                        residential_address=residential_address,
                        contact_number=contact_number,
                        employer_name='Not Provided',
                        employer_address='Not Provided',
                        next_of_kin_name=next_of_kin_name,
                        next_of_kin_contact_number=next_of_kin_contact_number,
                        next_of_kin_address=next_of_kin_address,
                        next_of_kin_relationship='Not Provided',
                        religion=religion,
                        chief=chief,
                        village=village,
                        tribe=tribe,
                        admission_datetime=admission_dt,
                        referring_doctor_hospital=referring,
                        diagnosis=diagnosis,
                        treatment=treatment,
                        doctor_name=handling_doctor,
                        consultant_name=consultant,
                        pharmacy_name=pharmacy,
                        discharge_datetime=discharge_dt,
                        status='Discharged' if discharge_dt else 'Admitted'
                    )
                    db.session.add(patient)
                    db.session.commit()
                    success_count += 1
                except Exception as e:
                    db.session.rollback()
                    error_count += 1
                    print(f"Error on row {index}: {str(e)}")
                    continue
            
            msg_parts = [f'Successfully imported {success_count} records.']
            if skipped_count > 0:
                msg_parts.append(f'Skipped {skipped_count} (missing hospital ID or duplicate).')
            if error_count > 0:
                msg_parts.append(f'{error_count} rows had errors.')
            
            flash_type = 'success' if error_count == 0 and skipped_count == 0 else 'warning'
            flash(' '.join(msg_parts), flash_type)
            return redirect(url_for('patients.list_patients'))
            
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            
    return render_template('patients/import.html', title='Import Database', form=form)

