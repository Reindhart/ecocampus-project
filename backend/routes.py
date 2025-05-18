from flask import render_template, request, redirect, url_for, flash, session
from .models import db, Usuario
from werkzeug.security import generate_password_hash, check_password_hash

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

    @app.route('/reportes')
    def reportes():
        if 'usuario_id' not in session:
            return redirect(url_for('login'))
        return render_template('reportes.html', usuario=session['usuario_nombre'])

    @app.route('/actividades')
    def actividades():
        return render_template('actividades.html')

    @app.route('/mapa')
    def mapa():
        return render_template('mapa.html')

    @app.route('/notificaciones')
    def notificaciones():
        return render_template('notificaciones.html')

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
    
    @app.route('/menu')
    def menu():
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para acceder al menú.')
            return redirect(url_for('login'))
        return render_template('menu.html')


