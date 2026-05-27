from flask import render_template, url_for, flash, redirect, Blueprint
from flask_login import login_required, current_user
from app import db
from app.models.models import Patient, Ward, Transfer
from app.transfers.forms import TransferForm
from app.auth.utils import role_required

transfers = Blueprint('transfers', __name__)

@transfers.route('/patient/<int:patient_id>/transfer', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'CMO', 'Sister In Charge'])
def transfer_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    if patient.status != 'Admitted':
        flash('Only admitted patients can be transferred.', 'warning')
        return redirect(url_for('patients.list_patients'))

    # If Sister In Charge, ensure they are in the ward they manage
    if current_user.role_obj.name == 'Sister In Charge' and patient.ward_id != current_user.ward_id:
        flash('You can only transfer patients from your own ward.', 'danger')
        return redirect(url_for('patients.list_patients'))

    form = TransferForm()
    # Destination wards can be any ward except the current one
    all_wards = Ward.query.filter(Ward.id != patient.ward_id).all()
    form.to_ward.choices = [(w.id, w.name) for w in all_wards]

    if form.validate_on_submit():
        from_ward_id = patient.ward_id
        to_ward_id = form.to_ward.data
        to_ward = Ward.query.get(to_ward_id)

        if to_ward.is_full:
            flash(f'Destination ward {to_ward.name} is currently at full capacity ({to_ward.capacity}).', 'danger')
            return redirect(url_for('transfers.transfer_patient', patient_id=patient_id))

        patient.ward_id = to_ward_id
        transfer = Transfer(
            patient_id=patient.id,
            from_ward_id=from_ward_id,
            to_ward_id=to_ward_id,
            transferred_by=current_user.id
        )
        db.session.add(transfer)
        db.session.commit()
        flash('Patient transferred successfully!', 'success')
        return redirect(url_for('patients.list_patients'))

    return render_template('transfers/transfer.html', title='Transfer Patient', form=form, patient=patient)
