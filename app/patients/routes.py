from flask import render_template, url_for, flash, redirect, Blueprint, request
from flask_login import login_required, current_user
from app import db
from app.models.models import (Patient, Ward, Admission, Discharge, Transfer, Race, MaritalStatus, 
                              Occupation, ReferringDoctorHospital, Consultant, Pharmacy)
from app.patients.forms import PatientRegistrationForm, AdmissionForm, DischargeForm, ImportForm
from app.auth.utils import role_required
import os
import pandas as pd
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

@patients.route('/patients')
@login_required
def list_patients():
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = Patient.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            (Patient.surname.ilike(f'%{search}%')) | 
            (Patient.first_names.ilike(f'%{search}%')) | 
            (Patient.hospital_id.ilike(f'%{search}%'))
        )
    
    if status:
        query = query.filter(Patient.status == status)
        
    all_patients = query.all()
    return render_template('patients/list_patients.html', patients=all_patients, search=search, status=status)

@patients.route('/patient/<int:patient_id>')
@login_required
def view_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patients/detail.html', patient=patient)

@patients.route('/patient/register', methods=['GET', 'POST'])
@login_required
def register_patient():
    form = PatientRegistrationForm()
    if form.validate_on_submit():
        try:
            # Generate hospital ID
            hospital_id = generate_hospital_id()
            
            # Create new patient with all fields
            patient = Patient(
                hospital_id=hospital_id,
                surname=form.surname.data,
                first_names=form.first_names.data,
                date_of_birth=form.date_of_birth.data,
                age=datetime.now().year - form.date_of_birth.data.year,  # Calculate age
                sex=form.sex.data,
                race=Race.query.get(form.race.data).name,
                marital_status=MaritalStatus.query.get(form.marital_status.data).name,
                occupation=Occupation.query.get(form.occupation.data).name,
                residential_address=form.residential_address.data,
                contact_number=form.contact_number.data,
                employer_name=form.employer_name.data or '',
                employer_address=form.employer_address.data or '',
                next_of_kin_name=form.next_of_kin_name.data,
                next_of_kin_address=form.next_of_kin_address.data,
                next_of_kin_relationship=form.next_of_kin_relationship.data,
                admission_datetime=form.admission_datetime.data,
                referring_doctor_hospital=ReferringDoctorHospital.query.get(form.referring_doctor_hospital.data).name,
                diagnosis=form.diagnosis.data,
                doctor_name=form.doctor_name.data,
                consultant_name=Consultant.query.get(form.consultant_name.data).name,
                pharmacy_name=Pharmacy.query.get(form.pharmacy_name.data).name,
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
        patient.discharge_datetime = form.discharge_datetime.data
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

@patients.route('/patient/<int:patient_id>/history')
@login_required
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    admissions = Admission.query.filter_by(patient_id=patient_id).order_by(Admission.timestamp.desc()).all()
    transfers = Transfer.query.filter_by(patient_id=patient_id).order_by(Transfer.timestamp.desc()).all()
    discharges = Discharge.query.filter_by(patient_id=patient_id).order_by(Discharge.timestamp.desc()).all()
    
    # Combine and sort all events by timestamp
    events = []
    for a in admissions:
        events.append({'type': 'Admission', 'timestamp': a.timestamp, 'ward': a.ward.name, 'by': a.user.name})
    for t in transfers:
        events.append({'type': 'Transfer', 'timestamp': t.timestamp, 'from_ward': t.from_ward.name, 'to_ward': t.to_ward.name, 'by': t.user.name})
    for d in discharges:
        events.append({'type': 'Discharge', 'timestamp': d.timestamp, 'ward': d.ward.name, 'by': d.user.name, 'notes': d.notes})
        
    events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('patients/history.html', patient=patient, events=events)

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
    flash(f'Patient {patient.name} has been removed from the active system.', 'success')
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
                
            # Map to Patient models
            success_count = 0
            skipped_count = 0
            for index, row in df.iterrows():
                try:
                    def get_val(col_names, default=None):
                        for c in col_names:
                            if c in df.columns and pd.notna(row[c]) and str(row[c]).strip():
                                return str(row[c]).strip()
                        return default

                    hospital_id = get_val(['hospital name', 'hospital_id', 'Hospital Name', 'Hospital ID', 'Hospital Number', 'hospital number'])
                    
                    if not hospital_id:
                        skipped_count += 1
                        continue
                        
                    # Check if already exists
                    if Patient.query.filter_by(hospital_id=hospital_id).first():
                        skipped_count += 1
                        continue

                    surname = get_val(['surname', 'Surname']) or 'Missing'
                    first_names = get_val(['name(s)', 'first_names', 'Name', 'First Name']) or 'Missing'
                    dob_str = get_val(['date of birth', 'DOB', 'Date of Birth'])
                    dob = pd.to_datetime(dob_str).date() if dob_str else datetime.now().date()
                    age_str = get_val(['age', 'Age'])
                    age = int(float(age_str)) if age_str and str(age_str).replace('.','',1).isdigit() else 0
                    sex = get_val(['sex', 'Sex', 'Gender']) or 'Missing'
                    race = get_val(['race', 'Race']) or 'Not Applicable'
                    marital_status = get_val(['marital status', 'Marital Status']) or 'Not Applicable'
                    occupation = get_val(['occupation', 'Occupation']) or 'Not Applicable'
                    residential_address = get_val(['residential address', 'Residential Address']) or 'Missing'
                    contact_number = get_val(['contact number', 'Contact Number']) or 'Missing'
                    employer_address = get_val(["employer's name and address", 'Employer Address']) or 'Missing'
                    next_of_kin_address = get_val(['next of kin name and address', 'Next of Kin Address']) or 'Missing'
                    relationship = get_val(['relationship', 'Relationship']) or 'Missing'
                    religion = get_val(['religion', 'Religion'], 'Not Applicable')
                    chief = get_val(['chief', 'Chief'], 'Not Applicable')
                    village = get_val(['village', 'Village'], 'Not Applicable')
                    tribe = get_val(['tribe', 'Tribe'], 'Not Applicable')
                    referring = get_val(['Name of Doctor/Referring Hospital', 'Referring Hospital']) or 'Not Applicable'
                    pharmacy = get_val(['name of pharmacy', 'Pharmacy']) or 'Not Applicable'
                    consultant = get_val(['name of consultant', 'Consultant']) or 'Not Applicable'
                    handling_doctor = get_val(['name of doctor', 'Doctor']) or 'Not Applicable'
                    diagnosis = get_val(['Diagnosis of patient', 'Diagnosis']) or 'Missing'
                    
                    admission_dt_str = get_val(['admission date and time', 'Admission Date'])
                    admission_dt = pd.to_datetime(admission_dt_str).to_pydatetime() if admission_dt_str else datetime.now()

                    discharge_dt_str = get_val(['date and time of discharge, transfer, or death', 'Discharge Date'])
                    discharge_dt = pd.to_datetime(discharge_dt_str).to_pydatetime() if discharge_dt_str else None

                    # If they don't exist in the dropdown tables, add them!
                    if not Race.query.filter_by(name=race).first():
                        db.session.add(Race(name=race))
                        db.session.commit()
                    if not MaritalStatus.query.filter_by(name=marital_status).first():
                        db.session.add(MaritalStatus(name=marital_status))
                        db.session.commit()
                    if not Occupation.query.filter_by(name=occupation).first():
                        db.session.add(Occupation(name=occupation))
                        db.session.commit()
                    if not ReferringDoctorHospital.query.filter_by(name=referring).first():
                        db.session.add(ReferringDoctorHospital(name=referring, type='Hospital'))
                        db.session.commit()
                    if not Consultant.query.filter_by(name=consultant).first():
                        db.session.add(Consultant(name=consultant))
                        db.session.commit()
                    if not Pharmacy.query.filter_by(name=pharmacy).first():
                        db.session.add(Pharmacy(name=pharmacy))
                        db.session.commit()

                    patient = Patient(
                        hospital_id=hospital_id,
                        surname=surname,
                        first_names=first_names,
                        date_of_birth=dob,
                        age=age,
                        sex=sex,
                        race=race,
                        marital_status=marital_status,
                        occupation=occupation,
                        residential_address=residential_address,
                        contact_number=contact_number,
                        employer_name='', # combined
                        employer_address=employer_address,
                        next_of_kin_name='Not Provided', # combined
                        next_of_kin_address=next_of_kin_address,
                        next_of_kin_relationship=relationship,
                        religion=religion,
                        chief=chief,
                        village=village,
                        tribe=tribe,
                        admission_datetime=admission_dt,
                        referring_doctor_hospital=referring,
                        diagnosis=diagnosis,
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
                    print(f"Error on row {index}: {str(e)}")
                    continue
            
            if skipped_count > 0:
                flash(f'Successfully imported {success_count} records. Skipped {skipped_count} records due to missing hospital IDs or duplicates.', 'warning')
            else:
                flash(f'Successfully imported all {success_count} records.', 'success')
            return redirect(url_for('patients.list_patients'))
            
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            
    return render_template('patients/import.html', title='Import Database', form=form)
