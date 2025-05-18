from flask import render_template, redirect, url_for, request, flash

def init_routes(app):
    @app.route('/')
    def inicio():
        return render_template('inicio.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Aquí va lógica de login
            return redirect(url_for('reportes'))
        return render_template('login.html')

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            # Aquí va lógica de registro
            return redirect(url_for('login'))
        return render_template('signup.html')

    @app.route('/reportes')
    def reportes():
        return render_template('reportes.html')

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
        return render_template('perfil.html')
