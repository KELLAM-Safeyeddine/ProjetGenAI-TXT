from flask import Blueprint, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import Vehicle
from app.forms import VehicleForm, DeleteForm
from app.services.manual_access import link_manual
from app.services.vehicle_catalog import allowed_public_catalog

bp = Blueprint('vehicles', __name__)

def owned_vehicle(vehicle_id):
    return db.first_or_404(db.select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.user_id == current_user.id))

@bp.get('/api/vehicle-catalog')
@login_required
def catalog():
    return jsonify(vehicles=allowed_public_catalog())

def vehicle_form_page(form, title, vehicle=None):
    legacy = form.legacy
    return render_template('vehicle_form.html',form=form,title=title,legacy=legacy,vehicle=vehicle), 422 if form.errors else 200

@bp.get('/dashboard')
@login_required
def dashboard():
    vehicles = db.session.scalars(db.select(Vehicle).where(Vehicle.user_id == current_user.id).order_by(Vehicle.id.desc())).all()
    operations = [m for v in vehicles for m in v.maintenance]
    return render_template('dashboard.html', vehicles=vehicles, operations=operations)

@bp.get('/vehicles')
@login_required
def index():
    vehicles = db.session.scalars(db.select(Vehicle).where(Vehicle.user_id == current_user.id).order_by(Vehicle.id.desc())).all()
    return render_template('vehicles.html', vehicles=vehicles)

@bp.route('/vehicles/new', methods=['GET','POST'])
@login_required
def create():
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(user_id=current_user.id)
        form.populate_obj(vehicle)
        link_manual(vehicle)
        db.session.add(vehicle)
        db.session.commit()
        flash('Véhicule ajouté.', 'success')
        return redirect(url_for('vehicles.index'))
    return vehicle_form_page(form,'Ajouter un véhicule')

@bp.route('/vehicles/<int:vehicle_id>/edit', methods=['GET','POST'])
@login_required
def edit(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        maximum = max((m.mileage for m in vehicle.maintenance), default=0)
        if form.mileage.data is not None and form.mileage.data < maximum:
            form.mileage.errors.append('Le compteur doit rester au moins égal aux opérations enregistrées.')
        else:
            form.populate_obj(vehicle)
            link_manual(vehicle)
            db.session.commit()
            flash('Véhicule mis à jour. Les échéances sont recalculées.', 'success')
            return redirect(url_for('vehicles.index'))
    return vehicle_form_page(form,'Modifier le véhicule',vehicle)

@bp.route('/vehicles/<int:vehicle_id>/delete', methods=['GET','POST'])
@login_required
def delete(vehicle_id):
    vehicle = owned_vehicle(vehicle_id)
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(vehicle)
        db.session.commit()
        flash('Véhicule et entretiens associés supprimés.', 'success')
        return redirect(url_for('vehicles.index'))
    return render_template('form.html', form=form, title=f'Supprimer {vehicle.brand} {vehicle.model}',
                           description=f'Les {len(vehicle.maintenance)} entretiens associés seront également supprimés.', danger=True), 422 if form.errors else 200
