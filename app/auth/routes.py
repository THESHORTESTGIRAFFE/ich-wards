from flask import render_template, url_for, flash, redirect, request, Blueprint
from urllib.parse import urlparse, urljoin
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models.models import User, Role, Ward
from app.auth.forms import LoginForm, UserRegistrationForm, UserUpdateForm
from app.auth.utils import role_required

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/users')
@login_required
@role_required(['Admin'])
def manage_users():
    users = User.query.all()
    return render_template('auth/manage_users.html', users=users)

@auth.route('/user/new', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def create_user():
    form = UserRegistrationForm()
    form.role.choices = [(r.id, r.name) for r in Role.query.all()]
    form.ward.choices = [(0, 'None')] + [(w.id, w.name) for w in Ward.query.all()]
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        ward_id = form.ward.data if form.ward.data != 0 else None
        user = User(name=form.name.data, email=form.email.data, password_hash=hashed_pw, role_id=form.role.data, ward_id=ward_id)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('auth.manage_users'))
    return render_template('auth/create_user.html', title='New User', form=form)

@auth.route('/user/<int:user_id>/update', methods=['GET', 'POST'])
@login_required
@role_required(['Admin'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserUpdateForm(original_email=user.email)
    form.role.choices = [(r.id, r.name) for r in Role.query.all()]
    form.ward.choices = [(0, 'None')] + [(w.id, w.name) for w in Ward.query.all()]
    if form.validate_on_submit():
        user.name = form.name.data
        user.email = form.email.data
        user.role_id = form.role.data
        user.ward_id = form.ward.data if form.ward.data != 0 else None
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('auth.manage_users'))
    elif request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.role.data = user.role_id
        form.ward.data = user.ward_id if user.ward_id else 0
    return render_template('auth/create_user.html', title='Update User', form=form)

@auth.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required(['Admin'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot delete yourself!', 'danger')
        return redirect(url_for('auth.manage_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('auth.manage_users'))
