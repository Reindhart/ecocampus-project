from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from .models import db, Usuario, Reporte, Actividad, Inscripcion
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os


def init_routes(app):
    @app.route('/')
    def inicio():
        return render_template('inicio.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form['username']
            correo = request.form['correo']
            contrasena = request.form['contrasena']

            existente = Usuario.query.filter_by(correo=correo).first()
            if existente:
                flash('Este correo ya está registrado.')
                return redirect(url_for('signup'))

            usuario = Usuario(
                username=username,
                correo=correo,
                contrasena=generate_password_hash(contrasena)
            )
            db.session.add(usuario)
            db.session.commit()
            flash('Cuenta creada correctamente. Ahora inicia sesión.')
            return redirect(url_for('login'))

        return render_template('signup.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            correo = request.form['correo']
            contrasena = request.form['contrasena']

            usuario = Usuario.query.filter_by(correo=correo).first()
            if usuario and check_password_hash(usuario.contrasena, contrasena):
                session['usuario_id'] = usuario.id
                session['usuario_nombre'] = usuario.username
                flash('Inicio de sesión exitoso.')
                return redirect(url_for('menu'))
            else:
                flash('Correo o contraseña incorrectos.')
                return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('Sesión cerrada correctamente.')
        return redirect(url_for('inicio'))
    
    @app.route('/menu')
    def menu():
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder al menú.')
            return redirect(url_for('login'))
        return render_template('menu.html')
    
    @app.route('/perfil')
    def perfil():
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para ver tu perfil.')
            return redirect(url_for('login'))

        usuario = Usuario.query.get(session['usuario_id'])

        if not usuario:
            flash('Usuario no encontrado.')
            return redirect(url_for('logout'))

        return render_template('perfil.html', usuario=usuario)
    
    @app.route('/perfil/reportes')
    def perfil_reportes():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        reportes = Reporte.query.filter_by(usuario_id=session['usuario_id']).all()
        return render_template('perfil_reportes.html', reportes=reportes)

    @app.route('/perfil/actividades')
    def perfil_actividades():
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.')
            return redirect(url_for('login'))

        inscripciones = Inscripcion.query.filter_by(usuario_id=session['usuario_id']).all()
        return render_template('perfil_actividades.html', inscripciones=inscripciones)


    @app.route('/reportes', methods=['GET', 'POST'])
    def reportes():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            area = request.form['area']
            tipo = request.form['tipo']
            descripcion = request.form['descripcion']
            comentario = request.form.get('comentario', '')
            archivo = request.files.get('evidencia')

            evidencia = ''
            if archivo and archivo.filename != '' and archivo_permitido(archivo.filename):
                nombre_archivo = secure_filename(archivo.filename)
                evidencia = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                ruta_absoluta = os.path.join(app.root_path, evidencia)
                archivo.save(ruta_absoluta)

            nuevo = Reporte(
                area=area,
                tipo=tipo,
                descripcion=descripcion,
                comentario=comentario,
                evidencia=evidencia.replace('frontend/', ''),  # Para usar con url_for
                fecha=datetime.now().strftime('%Y-%m-%d'),
                estado='pendiente',
                usuario_id=session['usuario_id']
            )
            db.session.add(nuevo)
            db.session.commit()
            flash(f'Reporte con el folio #{nuevo.id} fue enviado con éxito.')
            return redirect(url_for('menu'))

        return render_template('reportes.html')
    
    def archivo_permitido(nombre):
        return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


    @app.route('/actividades', methods=['GET', 'POST'])
    def actividades():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            actividad_id = request.form.get('actividad_id')
            ya_inscrito = Inscripcion.query.filter_by(
                usuario_id=session['usuario_id'],
                actividad_id=actividad_id
            ).first()

            if not ya_inscrito:
                inscripcion = Inscripcion(
                    usuario_id=session['usuario_id'],
                    actividad_id=actividad_id
                )
                db.session.add(inscripcion)
                db.session.commit()
                flash('Te has inscrito correctamente.')
            else:
                flash('Ya estás inscrito en esta actividad.')

            return redirect(url_for('actividades'))

        actividades = Actividad.query.all()
        inscritas = [i.actividad_id for i in Inscripcion.query.filter_by(usuario_id=session['usuario_id']).all()]
        return render_template('actividades.html', actividades=actividades, inscritas=inscritas)


    @app.route('/mapa')
    def mapa():
        return render_template('mapa.html')
    
    @app.route('/notificaciones')
    def notificaciones():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))

        # Ejemplo estático
        notificaciones = [
            {"mensaje": "Tu reporte #12 ha cambiado a estado 'En revisión'", "tipo": "info"},
            {"mensaje": "Nueva actividad disponible: Reforestación", "tipo": "success"},
            {"mensaje": "Tu actividad 'Reciclaje electrónico' inicia mañana", "tipo": "warning"}
        ]

        # notificaciones = Notificacion.query.filter_by(usuario_id=session['usuario_id']).all()

        return render_template('notificaciones.html', notificaciones=notificaciones)