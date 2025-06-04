from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

class BusinessUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    plantas = db.relationship('Plant', backref='business_unit', cascade="all, delete-orphan", lazy=True)
    sabores = db.relationship('Flavor', backref='business_unit', cascade="all, delete-orphan", lazy=True)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    bu_id = db.Column(db.Integer, db.ForeignKey('business_unit.id'), nullable=False)
    lineas = db.relationship('Line', backref='plant', cascade="all, delete-orphan", lazy=True)

class Line(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    pipes = db.Column(db.Integer, nullable=True)

class Flavor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    bu_id = db.Column(db.Integer, db.ForeignKey('business_unit.id'), nullable=False)

class EmpaqueExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bu_id = db.Column(db.Integer, db.ForeignKey('business_unit.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    linea = db.Column(db.String(150), nullable=True)  # Opcional, si se requiere luego
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data = db.Column(db.Text, nullable=False, default='{}')  # Guardará la "grid" como JSON

    bu = db.relationship('BusinessUnit', primaryjoin='EmpaqueExercise.bu_id == BusinessUnit.id', lazy=True)
    plant = db.relationship('Plant', primaryjoin='EmpaqueExercise.plant_id == Plant.id', lazy=True)

class DmeExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bu_id = db.Column(db.Integer, db.ForeignKey('business_unit.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    linea = db.Column(db.String(150), nullable=False)
    nombre = db.Column(db.String(150), nullable=True)  # Nuevo campo para el nombre
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data = db.Column(db.Text, nullable=False, default='{}')  # Guardará las capturas como JSON

    bu = db.relationship('BusinessUnit', primaryjoin='DmeExercise.bu_id == BusinessUnit.id', lazy=True)
    plant = db.relationship('Plant', primaryjoin='DmeExercise.plant_id == Plant.id', lazy=True)

class PesoRegistro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    linea_id = db.Column(db.Integer, db.ForeignKey('line.id'), nullable=False)
    usuario = db.Column(db.String(100), nullable=True)
    data = db.Column(db.Text, nullable=False, default='{}')  # Aquí se guarda todo lo demás como JSON

    linea = db.relationship('Line', backref='linea', lazy=True)
