from flask import render_template, url_for, flash, redirect, Blueprint
from flask_login import login_required
from app import db
from app.models.models import Ward
from app.wards.forms import WardForm
from app.auth.utils import role_required

wards = Blueprint('wards', __name__)

@wards.route('/wards')
@login_required
def list_wards():
    all_wards = Ward.query.all()
    return render_template('wards/manage_wards.html', wards=all_wards)

@wards.route('/ward/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def create_ward():
    form = WardForm()
    if form.validate_on_submit():
        ward = Ward(name=form.name.data, type=form.type.data, capacity=form.capacity.data)
        db.session.add(ward)
        db.session.commit()
        flash('Ward created successfully!', 'success')
        return redirect(url_for('wards.list_wards'))
    return render_template('wards/create_ward.html', title='New Ward', form=form)

@wards.route('/ward/<int:ward_id>/delete', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete_ward(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    if ward.patients:
        flash('Cannot delete a ward that has patients!', 'danger')
        return redirect(url_for('wards.list_wards'))
    db.session.delete(ward)
    db.session.commit()
    flash('Ward deleted successfully!', 'success')
    return redirect(url_for('wards.list_wards'))
