from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.forms import MaintenanceForm, DeleteForm
from app.models import Maintenance
from app.routes.vehicles import owned_vehicle

bp = Blueprint('maintenance', __name__)

def owned_maintenance(maintenance_id):
    operation = db.get_or_404(Maintenance, maintenance_id)
    owned_vehicle(operation.vehicle_id)
    return operation

def coherent(form, vehicle, operation=None):
    if vehicle.mileage is not None and form.mileage.data > vehicle.mileage:
        form.mileage.errors.append('Actualisez le compteur du véhicule avant de saisir un kilométrage supérieur.')
    for other in vehicle.maintenance:
        if operation and operation.id == other.id:
            continue
        if (other.date < form.date.data and other.mileage > form.mileage.data) or (other.date > form.date.data and other.mileage < form.mileage.data):
            form.mileage.errors.append('Kilométrage incohérent avec la chronologie des entretiens.')
            break
    return not form.errors

@bp.get('/vehicles/<int:vehicle_id>/maintenance')
@login_required
def index(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    operations = db.session.scalars(db.select(Maintenance).where(Maintenance.vehicle_id == vehicle.id).order_by(Maintenance.date.desc(),Maintenance.id.desc())).all()
    return render_template('maintenance.html', vehicle=vehicle, operations=operations)

@bp.route('/vehicles/<int:vehicle_id>/maintenance/new', methods=['GET','POST'])
@login_required
def create(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    form = MaintenanceForm()
    if form.validate_on_submit() and coherent(form,vehicle):
        operation = Maintenance(vehicle_id=vehicle.id)
        form.populate_obj(operation)
        db.session.add(operation)
        db.session.commit()
        flash('Entretien enregistré.', 'success')
        return redirect(url_for('maintenance.index', vehicle_id=vehicle.id))
    return render_template('form.html', form=form, title='Enregistrer un entretien', description='Échéances facultatives : recopiez le carnet constructeur. Aucun intervalle n’est calculé automatiquement.'), 422 if form.errors else 200

@bp.route('/maintenance/<int:maintenance_id>/edit', methods=['GET','POST'])
@login_required
def edit(maintenance_id):
    operation = owned_maintenance(maintenance_id)
    form = MaintenanceForm(obj=operation)
    if form.validate_on_submit() and coherent(form, operation.vehicle, operation):
        form.populate_obj(operation)
        db.session.commit()
        return redirect(url_for('maintenance.index', vehicle_id=operation.vehicle_id))
    return render_template('form.html', form=form, title='Modifier l’entretien'), 422 if form.errors else 200

@bp.route('/maintenance/<int:maintenance_id>/delete', methods=['GET','POST'])
@login_required
def delete(maintenance_id):
    operation = owned_maintenance(maintenance_id)
    form = DeleteForm()
    if form.validate_on_submit():
        vehicle_id = operation.vehicle_id
        db.session.delete(operation)
        db.session.commit()
        return redirect(url_for('maintenance.index', vehicle_id=vehicle_id))
    return render_template('form.html', form=form, title='Supprimer cet entretien', danger=True), 422 if form.errors else 200
