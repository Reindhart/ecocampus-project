from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(120), unique=True, nullable=False)
    contrasena = db.Column(db.String(200), nullable=False)
    es_admin = db.Column(db.Boolean, default=False)

class Reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    comentario = db.Column(db.String(200))
    evidencia = db.Column(db.String(200))  # Ruta del archivo
    fecha = db.Column(db.String(10), nullable=False)
    estado = db.Column(db.String(20), default='pendiente')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

class Actividad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    area = db.Column(db.String(100))
    fecha_hora_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 
    archivada = db.Column(db.Boolean, default=False)

class Inscripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    actividad_id = db.Column(db.Integer, db.ForeignKey('actividad.id'))

    actividad = db.relationship('Actividad', backref='inscripciones')
    
class Notificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mensaje = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(50))  # info, alerta, éxito, etc.
    leida = db.Column(db.Boolean, default=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))