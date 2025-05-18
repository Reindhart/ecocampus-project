from . import db

class Reporte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(200), nullable=False)
    fecha = db.Column(db.String(10), nullable=False)
