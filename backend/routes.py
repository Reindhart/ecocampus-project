from flask import render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime, timedelta
from .models import db, Usuario, Reporte, Actividad, Inscripcion, Notificacion
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from sqlalchemy import or_
import os, json

def init_routes(app):
    @app.route('/')
    def inicio():
        
        if session.get('usuario_id'):        
            usuario = Usuario.query.filter_by(id=session['usuario_id']).first()
            if usuario:
                return redirect(url_for('menu'))
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
                session['es_admin'] = usuario.es_admin
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
            crear_notificacion("Tu reporte ha sido creado y está pendiente.", 'info', usuario_id=session['usuario_id'])
            return redirect(url_for('menu'))

        return render_template('reportes.html')
    
    def archivo_permitido(nombre):
        return '.' in nombre and nombre.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


    @app.route('/actividades', methods=['GET', 'POST'])
    def actividades():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        archivar_actividades_pasadas()

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
                
                actividad = Actividad.query.get(actividad_id)
                crear_notificacion(f"Te has inscrito en la actividad: {actividad.titulo}", 'success', usuario_id=session['usuario_id'])
                flash('Te has inscrito correctamente.')
            else:
                flash('Ya estás inscrito en esta actividad.')

            return redirect(url_for('actividades'))

        actividades = Actividad.query.filter_by(archivada=False).order_by(Actividad.fecha_hora_inicio.asc()).all()
        inscritas = [i.actividad_id for i in Inscripcion.query.filter_by(usuario_id=session['usuario_id']).all()]
        return render_template('actividades.html', actividades=actividades, inscritas=inscritas)


    @app.route('/mapa')
    def mapa():
        return render_template('mapa.html')
    
    @app.route('/notificaciones')
    def notificaciones():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))

        usuario_id = session['usuario_id']

        notificaciones = Notificacion.query.filter(
            or_(
                Notificacion.usuario_id == usuario_id,
                Notificacion.usuario_id == None  # también puedes usar `is_(None)`
            )
        ).order_by(Notificacion.fecha.desc()).all()  # Opcional: ordenadas por fecha

        return render_template('notificaciones.html', notificaciones=notificaciones)
    
    def crear_notificacion(mensaje, tipo='info', usuario_id=None):
        noti = Notificacion(
            mensaje=mensaje,
            tipo=tipo,
            usuario_id=usuario_id
        )
        db.session.add(noti)
        db.session.commit()
    
    
# ------------------------------------------------------------------------------------------------------------ #
#                                         ADMIN ROUTES                                                         #
# ------------------------------------------------------------------------------------------------------------ #

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('usuario_id') or not session.get('es_admin'):
                flash('Acceso restringido a administradores.')
                return redirect(url_for('menu'))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        return render_template('admin/dashboard.html')

    @app.route('/admin/puntos', methods=['GET', 'POST'])
    @admin_required
    def admin_puntos():
        ruta_json = os.path.join(current_app.root_path, '..', 'frontend', 'static', 'js', 'puntos.json')

        if not os.path.exists(ruta_json):
            flash(f'Archivo puntos.json no encontrado. Ruta: {ruta_json}', 'danger')
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            tipo = request.form['tipo']
            lat = float(request.form['lat'])
            lng = float(request.form['lng'])

            with open(ruta_json, 'r', encoding='utf-8') as f:
                puntos = json.load(f)

            puntos.append({
                'nombre': nombre,
                'descripcion': descripcion,
                'lat': lat,
                'lng': lng,
                'tipo': tipo
            })

            with open(ruta_json, 'w', encoding='utf-8') as f:
                json.dump(puntos, f, ensure_ascii=False, indent=2)

            crear_notificacion(f"Se ha agregado un nuevo punto de interés: {nombre}", 'info')
            flash('Punto agregado correctamente.')
            return redirect(url_for('admin_puntos'))

        return render_template('admin/puntos.html')

    @app.route('/admin/reportes')
    @admin_required
    def admin_reportes():
        reportes = Reporte.query.order_by(Reporte.fecha.desc()).all()
        return render_template('admin/reportes.html', reportes=reportes)
    
    @app.route('/admin/reportes/<int:reporte_id>/actualizar', methods=['POST'])
    @admin_required
    def actualizar_reporte(reporte_id):
        nuevo_estado = request.form.get('estado')
        comentario = request.form.get('comentario')

        reporte = Reporte.query.get_or_404(reporte_id)
        reporte.estado = nuevo_estado
        if comentario:
            reporte.comentario = comentario
        db.session.commit()
        if nuevo_estado == 'resuelto':
            crear_notificacion(f"Tu reporte fue actualizado a estado: {nuevo_estado}.", 'success', usuario_id=reporte.usuario_id)
        if nuevo_estado == 'en proceso':
            crear_notificacion(f"Tu reporte fue actualizado a estado: {nuevo_estado}.", 'warning', usuario_id=reporte.usuario_id)
        flash('Reporte actualizado correctamente.')
        return redirect(url_for('admin_reportes'))

    @app.route('/admin/actividades')
    @admin_required
    def admin_actividades():
        archivar_actividades_pasadas()  # Reutilizamos la función

        mostrar_archivadas = request.args.get('archivadas') == '1'

        actividades = Actividad.query.filter_by(
            archivada=mostrar_archivadas
        ).order_by(Actividad.fecha_hora_inicio.asc()).all()

        return render_template('admin/actividades.html', actividades=actividades, mostrar_archivadas=mostrar_archivadas)
    
    @app.route('/admin/actividades/crear', methods=['GET', 'POST'])
    @admin_required
    def crear_actividad():
        if request.method == 'POST':
            titulo = request.form['titulo']
            descripcion = request.form['descripcion']
            area = request.form['area']
            fecha_str = request.form['fecha_hora_inicio']
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            if fecha < datetime.now():
                flash('La fecha y hora deben ser futuras.', 'danger')
                return render_template('admin/actividad_form.html', accion='Crear', now=datetime.now())

            nueva = Actividad(titulo=titulo, descripcion=descripcion, area=area, fecha_hora_inicio=fecha)
            db.session.add(nueva)
            db.session.commit()
            crear_notificacion(f"Nueva actividad disponible: {nueva.titulo}", 'info')
            flash('Actividad creada correctamente.')
            return redirect(url_for('admin_actividades'))

        return render_template('admin/actividad_form.html', accion='Crear', now=datetime.now())

    @app.route('/admin/actividades/<int:id>/editar', methods=['GET', 'POST'])
    @admin_required
    def editar_actividad(id):
        actividad = Actividad.query.get_or_404(id)

        if request.method == 'POST':
            actividad.titulo = request.form['titulo']
            actividad.descripcion = request.form['descripcion']
            actividad.area = request.form['area']
            fecha_str = request.form['fecha_hora_inicio']
            fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M')
            if fecha < datetime.now():
                flash('La fecha y hora deben ser futuras.', 'danger')
                return render_template('admin/actividad_form.html', accion='Editar', now=datetime.now(), actividad=actividad)
            actividad.fecha_hora_inicio = fecha
            
            
            db.session.commit()
            flash('Actividad actualizada correctamente.')
            return redirect(url_for('admin_actividades'))

        return render_template('admin/actividad_form.html', accion='Editar', actividad=actividad, now=datetime.now())

    @app.route('/admin/actividades/<int:id>/archivar', methods=['POST'])
    @admin_required
    def archivar_actividad(id):
        actividad = Actividad.query.get_or_404(id)
        actividad.archivada = not actividad.archivada
        db.session.commit()
        flash(f"Actividad {'archivada' if actividad.archivada else 'desarchivada'} correctamente.")
        return redirect(url_for('admin_actividades'))

    def archivar_actividades_pasadas():
        ahora = datetime.now()
        actividades_pasadas = Actividad.query.filter(
            Actividad.fecha_hora_inicio < ahora,
            Actividad.archivada == False
        ).all()

        for actividad in actividades_pasadas:
            actividad.archivada = True

        if actividades_pasadas:
            db.session.commit()
