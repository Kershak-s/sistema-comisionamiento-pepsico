import os
import json
from datetime import datetime
from datetime import datetime as dt
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, BusinessUnit, Plant, Line, Flavor, EmpaqueExercise

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Añadir datetime a todas las plantillas
@app.context_processor
def inject_now():
    return {'now': dt.now()}

# Crear las tablas y el usuario admin si no existe
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', password=generate_password_hash('PEPCODE'), role='admin')
        db.session.add(admin_user)
        db.session.commit()

# ===================== RUTAS DE AUTENTICACIÓN Y DASHBOARD =====================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash("Usuario o contraseña inválidos")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/deep_dive')
def deep_dive():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('deep_dive.html')

@app.route('/comicionamiento')
def comicionamiento():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('comicionamiento.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===================== RUTAS DE ADMINISTRACIÓN (USUARIOS, BU, PLANTAS, ETC.) =====================

@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')
        if User.query.filter_by(username=username).first():
            flash("El usuario ya existe")
        else:
            new_user = User(username=username, password=generate_password_hash(password), role=role)
            db.session.add(new_user)
            db.session.commit()
            flash("Usuario creado correctamente")
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/business_units', methods=['GET', 'POST'])
def admin_business_units():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        bu_name = request.form['name']
        if BusinessUnit.query.filter_by(name=bu_name).first():
            flash("El BU ya existe")
        else:
            new_bu = BusinessUnit(name=bu_name)
            db.session.add(new_bu)
            db.session.commit()
            flash("BU creado correctamente")
    bus = BusinessUnit.query.all()
    return render_template('admin_business_units.html', bus=bus)

@app.route('/admin/business_units/<int:bu_id>/sabores', methods=['GET', 'POST'])
def admin_sabores(bu_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    bu = BusinessUnit.query.get_or_404(bu_id)
    if request.method == 'POST':
        flavor_name = request.form['name']
        new_flavor = Flavor(name=flavor_name, bu_id=bu.id)
        db.session.add(new_flavor)
        db.session.commit()
        flash("Sabor agregado correctamente")
    return render_template('admin_sabores.html', bu=bu)

@app.route('/admin/business_units/<int:bu_id>/plantas', methods=['GET', 'POST'])
def admin_plantas(bu_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    bu = BusinessUnit.query.get_or_404(bu_id)
    if request.method == 'POST':
        plant_name = request.form['name']
        new_plant = Plant(name=plant_name, bu_id=bu.id)
        db.session.add(new_plant)
        db.session.commit()
        flash("Planta agregada correctamente")
    return render_template('admin_plantas.html', bu=bu)

@app.route('/admin/plantas/<int:plant_id>/lineas', methods=['GET', 'POST'])
def admin_lineas(plant_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    plant = Plant.query.get_or_404(plant_id)
    if request.method == 'POST':
        line_name = request.form['name']
        new_line = Line(name=line_name, plant_id=plant.id)
        db.session.add(new_line)
        db.session.commit()
        flash("Línea agregada correctamente")
    return render_template('admin_lineas.html', plant=plant)

# ===================== RUTAS PARA EL EJERCICIO "EFF DE EMPAQUE" =====================

@app.route('/eff_empaque', methods=['GET'])
def eff_empaque():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '')
    exercises = EmpaqueExercise.query.order_by(EmpaqueExercise.created_at.desc()).all()
    bus = BusinessUnit.query.all()
    plants = Plant.query.all()
    return render_template('eff_empaque.html', exercises=exercises, query=query, bus=bus, plants=plants)

@app.route('/eff_empaque/new', methods=['GET', 'POST'])
def new_eff_empaque():
    if 'user_id' not in session:
        flash("Debe iniciar sesión para crear un ejercicio")
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        # Mostrar el formulario para seleccionar BU y planta
        bus = BusinessUnit.query.all()
        plants = Plant.query.all()
        return render_template('new_eff_empaque.html', bus=bus, plants=plants)
    
    # Si es POST, procesamos la creación del ejercicio
    bu_id = request.form.get('bu_id')
    plant_id = request.form.get('plant_id')
    if not bu_id or not plant_id:
        flash("Debe seleccionar BU y Planta")
        return redirect(url_for('eff_empaque'))
    default_data = {
        "captures": [
            {
                "sabor": "",
                "tubo": "",
                "peso_gr": 0,
                "bpm_actual": 0,
                "tiempo": 0,
                "total_pq": 0,
                "total_pq_buenos": 0,
                "bpm_propuesta": 0,
                "bpm_global": 0,
                "seasoning": "",
                "eff_std_empaque": 0,
                "pq_global": 0,
                "eff_actual_empaque": 0,
                "mejora_propuesta": 0,
                "eff_propuesta": 0,
                "std_pt": 0,
                "actual_pt": 0,
                "propuesta_pt": 0,
                "global_pt": 0,
                "desperdicio": ""
            }
        ]
    }
    try:
        exercise = EmpaqueExercise(bu_id=bu_id, plant_id=plant_id, data=json.dumps(default_data))
        db.session.add(exercise)
        db.session.commit()
        flash("Ejercicio creado exitosamente")
        return redirect(url_for('excel_eff_empaque', exercise_id=exercise.id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear el ejercicio: {str(e)}")
        return redirect(url_for('eff_empaque'))

@app.route('/eff_empaque/<int:exercise_id>/view', methods=['GET'])
def view_eff_empaque(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    return render_template('eff_empaque_detail.html', exercise=exercise, data=data)

@app.route('/new_eff_empaque', methods=['POST'])
def new_eff_empaque_redirect():
    """Ruta de compatibilidad para redireccionar al nuevo formato de Excel"""
    if 'user_id' not in session:
        flash("Debe iniciar sesión para crear un ejercicio")
        return redirect(url_for('login'))
    bu_id = request.form.get('bu_id')
    plant_id = request.form.get('plant_id')
    if not bu_id or not plant_id:
        flash("Debe seleccionar BU y Planta")
        return redirect(url_for('eff_empaque'))
    default_data = {
        "captures": [
            {
                "sabor": "",
                "tubo": "",
                "peso_gr": 0,
                "bpm_actual": 0,
                "tiempo": 0,
                "total_pq": 0,
                "total_pq_buenos": 0,
                "bpm_propuesta": 0,
                "bpm_global": 0,
                "seasoning": "",
                "eff_std_empaque": 0,
                "pq_global": 0,
                "eff_actual_empaque": 0,
                "mejora_propuesta": 0,
                "eff_propuesta": 0,
                "std_pt": 0,
                "actual_pt": 0,
                "propuesta_pt": 0,
                "global_pt": 0,
                "desperdicio": ""
            }
        ]
    }
    try:
        exercise = EmpaqueExercise(bu_id=bu_id, plant_id=plant_id, data=json.dumps(default_data))
        db.session.add(exercise)
        db.session.commit()
        flash("Ejercicio creado exitosamente")
        return redirect(url_for('excel_eff_empaque', exercise_id=exercise.id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear el ejercicio: {str(e)}")
        return redirect(url_for('eff_empaque'))

@app.route('/eff_empaque/<int:exercise_id>/delete', methods=['POST'])
def delete_eff_empaque(exercise_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    flash("Ejercicio eliminado")
    return redirect(url_for('eff_empaque'))

@app.route('/eff_empaque/<int:exercise_id>/excel', methods=['GET', 'POST'])
def excel_eff_empaque(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    
    if request.method == 'POST':
        try:
            # Recopilar datos del formulario
            # Primera fila
            sabores_list = request.form.getlist('sabor[]')
            tubos_list = request.form.getlist('tubo[]')
            peso_grs_list = request.form.getlist('peso_gr[]')
            bpm_actuals_list = request.form.getlist('bpm_actual[]')
            tiempos_list = request.form.getlist('tiempo[]')
            total_pqs_list = request.form.getlist('total_pq[]')
            total_pq_buenos_list = request.form.getlist('total_pq_buenos[]')
            bpm_propuestas_list = request.form.getlist('bpm_propuesta[]')
            bpm_globals_list = request.form.getlist('bpm_global[]')
            
            # Segunda fila
            seasonings_list = request.form.getlist('seasoning[]')
            eff_std_empaques_list = request.form.getlist('eff_std_empaque[]')
            pq_global_list = request.form.getlist('pq_global[]')
            desperdicios_list = request.form.getlist('desperdicio[]')
            
            # Tercera fila
            eff_actual_list = request.form.getlist('eff_actual_empaque[]')
            mejora_propuestas_list = request.form.getlist('mejora_propuesta[]')
            eff_propuesta_list = request.form.getlist('eff_propuesta[]')
            
            # Cuarta fila
            std_pt_list = request.form.getlist('std_pt[]')
            actual_pt_list = request.form.getlist('actual_pt[]')
            propuesta_pt_list = request.form.getlist('propuesta_pt[]')
            global_pt_list = request.form.getlist('global_pt[]')
            
            captures = []
            n = len(sabores_list)
            
            for i in range(n):
                try:
                    # Convertir valores a números
                    peso_val = float(peso_grs_list[i]) if peso_grs_list[i] != "" else 0
                    bpm_actual_val = float(bpm_actuals_list[i]) if bpm_actuals_list[i] != "" else 0
                    tiempo_val = float(tiempos_list[i]) if tiempos_list[i] != "" else 0
                    total_pq_val = float(total_pqs_list[i]) if total_pqs_list[i] != "" else 0
                    total_pq_buenos_val = float(total_pq_buenos_list[i]) if total_pq_buenos_list[i] != "" else 0
                    bpm_propuesta_val = float(bpm_propuestas_list[i]) if bpm_propuestas_list[i] != "" else 0
                    bpm_global_val = float(bpm_globals_list[i]) if bpm_globals_list[i] != "" else 0
                    eff_std_empaque_val = float(eff_std_empaques_list[i]) if eff_std_empaques_list[i] != "" else 0
                    mejora_propuesta_val = float(mejora_propuestas_list[i]) if mejora_propuestas_list[i] != "" else 0
                    
                    # Valores calculados
                    pq_global_val = float(pq_global_list[i]) if pq_global_list[i] != "" else 0
                    eff_actual_val = float(eff_actual_list[i]) if eff_actual_list[i] != "" else 0
                    eff_propuesta_val = float(eff_propuesta_list[i]) if eff_propuesta_list[i] != "" else 0
                    std_pt_val = float(std_pt_list[i]) if std_pt_list[i] != "" else 0
                    actual_pt_val = float(actual_pt_list[i]) if actual_pt_list[i] != "" else 0
                    propuesta_pt_val = float(propuesta_pt_list[i]) if propuesta_pt_list[i] != "" else 0
                    global_pt_val = float(global_pt_list[i]) if global_pt_list[i] != "" else 0
                    
                except Exception as conv_err:
                    flash("Error en conversión numérica: " + str(conv_err))
                    return redirect(url_for('excel_eff_empaque', exercise_id=exercise_id))
                
                capture = {
                    "sabor": sabores_list[i],
                    "tubo": tubos_list[i],
                    "peso_gr": peso_val,
                    "bpm_actual": bpm_actual_val,
                    "tiempo": tiempo_val,
                    "total_pq": total_pq_val,
                    "total_pq_buenos": total_pq_buenos_val,
                    "bpm_propuesta": bpm_propuesta_val,
                    "bpm_global": bpm_global_val,
                    "seasoning": seasonings_list[i],
                    "eff_std_empaque": eff_std_empaque_val,
                    "pq_global": pq_global_val,
                    "eff_actual_empaque": eff_actual_val,
                    "mejora_propuesta": mejora_propuesta_val,
                    "eff_propuesta": eff_propuesta_val,
                    "std_pt": std_pt_val,
                    "actual_pt": actual_pt_val,
                    "propuesta_pt": propuesta_pt_val,
                    "global_pt": global_pt_val,
                    "desperdicio": desperdicios_list[i]
                }
                captures.append(capture)
                
            # Actualizar el ejercicio
            new_data = {"captures": captures}
            exercise.data = json.dumps(new_data)
            db.session.commit()
            flash("Ejercicio actualizado exitosamente")
            return redirect(url_for('view_eff_empaque', exercise_id=exercise.id))
            
        except Exception as e:
            flash("Error al guardar el ejercicio: " + str(e))
            return redirect(url_for('excel_eff_empaque', exercise_id=exercise_id))
    
    # Método GET
    data = json.loads(exercise.data)
    if "captures" not in data:
        data = {"captures": [data]}
    
    flavors = Flavor.query.filter_by(bu_id=exercise.bu_id).all()
    return render_template('excel_eff_empaque.html', exercise=exercise, data=data, flavors=flavors)

if __name__ == '__main__':
    app.run(debug=True)