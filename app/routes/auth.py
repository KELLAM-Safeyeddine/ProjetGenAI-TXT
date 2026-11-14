from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from app import db
from app.forms import RegisterForm, LoginForm, DeleteAccountForm
from app.models import User
from app.services.abuse_protection import locked, lock_response, login_failed, login_succeeded

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('vehicles.dashboard'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, role='user')
        user.set_password(form.password.data)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append('Cette adresse est déjà utilisée.')
        else:
            login_user(user)
            session.permanent = True
            return redirect(url_for('vehicles.dashboard'))
    return render_template('register.html', form=form), 422 if form.errors else 200

@bp.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('vehicles.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        if locked(form.email.data):
            return lock_response(form.email.data)
        user = db.session.scalar(db.select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            login_succeeded(form.email.data)
            login_user(user)
            session.permanent = True
            return redirect(url_for('vehicles.dashboard'))
        login_failed(form.email.data)
        form.password.errors.append('Adresse ou mot de passe incorrect.')
    return render_template('login.html', form=form), 422 if form.errors else 200

@bp.post('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@bp.route('/account/delete', methods=['GET','POST'])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.password.data):
            form.password.errors.append('Mot de passe incorrect.')
        else:
            user = current_user._get_current_object()
            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash('Votre compte et ses données ont été supprimés.', 'success')
            return redirect(url_for('index'))
    return render_template('form.html', form=form, title='Supprimer mon compte et toutes mes données', danger=True), 422 if form.errors else 200
