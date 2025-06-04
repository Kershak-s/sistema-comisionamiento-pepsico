import os
import json
from datetime import datetime
from datetime import datetime as dt
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, BusinessUnit, Plant, Line, Flavor, EmpaqueExercise, DmeExercise, PesoRegistro
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuración para subida de imágenes
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Asegurarse de que el directorio de uploads exista
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)

migrate = Migrate(app, db)

# Función para verificar si un archivo tiene una extensión permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Añadir datetime a todas las plantillas
@app.context_processor
def inject_now():
    return {'now': dt.now()}

# Añadir filtros personalizados
@app.template_filter('fromiso')
def from_iso_filter(date_string):
    try:
        return datetime.fromisoformat(date_string)
    except:
        return datetime.now()
        
@app.template_filter('tojson')
def to_json_filter(data):
    return json.dumps(data)

@app.template_filter('fromjson')
def from_json_filter(data):
    try:
        return json.loads(data)
    except:
        return {}

@app.template_filter('strftime')
def strftime_filter(date, format='%d/%m/%Y'):
    try:
        return date.strftime(format)
    except:
        return str(date)

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

@app.route('/admin/users/edit', methods=['POST'])
def admin_users_edit():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    user_id = request.form['user_id']
    user = User.query.get_or_404(user_id)
    user.username = request.form['username']
    user.role = request.form.get('role', 'user')
    password = request.form.get('password', '')
    if password:
        user.password = generate_password_hash(password)
    db.session.commit()
    flash("Usuario actualizado correctamente")
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete', methods=['POST'])
def admin_users_delete():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    user_id = request.form.get('user_id')
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash("No se puede eliminar el usuario administrador principal")
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash("Usuario eliminado correctamente")
    return redirect(url_for('admin_users'))

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
        tubos = request.form.get('tubos', type=int)  # Obtener la cantidad de tubos del formulario
        new_line = Line(name=line_name, plant_id=plant.id, pipes=tubos)
        db.session.add(new_line)
        db.session.commit()
        flash("Línea agregada correctamente")
    return render_template('admin_lineas.html', plant=plant)

@app.route('/admin/plantas/<int:plant_id>/lineas/<int:line_id>/delete', methods=['POST'])
def delete_linea(plant_id, line_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    line = Line.query.get_or_404(line_id)
    db.session.delete(line)
    db.session.commit()
    flash("Línea eliminada correctamente")
    return redirect(url_for('admin_lineas', plant_id=plant_id))

@app.route('/admin/plantas/<int:plant_id>/lineas/<int:line_id>/edit', methods=['POST'])
def edit_linea(plant_id, line_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    line = Line.query.get_or_404(line_id)
    line.name = request.form.get('name', line.name)
    line.pipes = request.form.get('tubos', line.pipes, type=int)  # Actualizar la cantidad de tubos si viene en el formulario
    db.session.commit()
    flash("Línea actualizada correctamente")
    return redirect(url_for('admin_lineas', plant_id=plant_id))

# ===================== RUTAS PARA EL EJERCICIO "EFF DE EMPAQUE" =====================

@app.route('/eff_empaque', methods=['GET'])
def eff_empaque():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '').strip().lower()
    exercises = EmpaqueExercise.query.order_by(EmpaqueExercise.created_at.desc()).all()
    if query:
        filtered = []
        for ex in exercises:
            bu_name = ex.bu.name.lower() if ex.bu and ex.bu.name else ''
            plant_name = ex.plant.name.lower() if ex.plant and ex.plant.name else ''
            linea = (ex.linea or '').lower() if hasattr(ex, 'linea') else ''
            if (query in bu_name) or (query in plant_name) or (query in linea):
                filtered.append(ex)
        exercises = filtered
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

@app.route('/eff_empaque/<int:exercise_id>/add_capture', methods=['POST'])
def add_capture_eff_empaque(exercise_id):
    if 'user_id' not in session:
        return abort(401)
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data) if exercise.data else {"captures": []}

    # Recibe los datos del modal
    sabor = request.form.get('sabor', '')
    tubo = request.form.get('tubo', '')
    peso_gr = float(request.form.get('peso_gr', 0))
    bpm_actual = float(request.form.get('bpm_actual', 0))
    tiempo = float(request.form.get('tiempo', 0))
    total_pq = int(request.form.get('total_pq', 0))
    total_pq_buenos = int(request.form.get('total_pq_buenos', 0))
    bpm_propuesta = int(request.form.get('bpm_propuesta', 0))
    bpm_global = int(request.form.get('bpm_global', 0))
    seasoning = float(request.form.get('seasoning', 0))
    eff_std_empaque = int(request.form.get('eff_std_empaque', 0))
    mejora_propuesta = int(request.form.get('mejora_propuesta', 0))

    nueva_captura = {
        "sabor": sabor,
        "tubo": tubo,
        "peso_gr": peso_gr,
        "bpm_actual": bpm_actual,
        "tiempo": tiempo,
        "total_pq": total_pq,
        "total_pq_buenos": total_pq_buenos,
        "bpm_propuesta": bpm_propuesta,
        "bpm_global": bpm_global,
        "seasoning": seasoning,
        "eff_std_empaque": eff_std_empaque,
        "mejora_propuesta": mejora_propuesta
    }

    data.setdefault("captures", []).append(nueva_captura)
    exercise.data = json.dumps(data)
    exercise.updated_at = datetime.now()
    db.session.commit()

    flash("Captura agregada exitosamente")
    return redirect(url_for('excel_eff_empaque', exercise_id=exercise_id))

def calcular_promedios(captures):
    n = len(captures)
    if n == 0:
        return {
            "eff_std_empaque": 0,
            "eff_actual_empaque": 0,
            "mejora_propuesta": 0,
            "eff_propuesta": 0,
            "std_pt": 0,
            "actual_pt": 0,
            "propuesta_pt": 0,
            "global_pt": 0,
            "desperdicio": 0,
        }
    def safe_div(a, b):
        try:
            return a / b if b else 0
        except:
            return 0
    return {
        "eff_std_empaque": sum(c.get("eff_std_empaque", 0) for c in captures) / n,
        "eff_actual_empaque": sum(safe_div(c.get("total_pq_buenos", 0), c.get("bpm_actual", 0)*60*c.get("tiempo", 0))*100 if c.get("bpm_actual", 0) and c.get("tiempo", 0) else 0 for c in captures) / n,
        "mejora_propuesta": sum(c.get("mejora_propuesta", 0) for c in captures) / n,
        "eff_propuesta": sum((safe_div(c.get("total_pq_buenos", 0), c.get("bpm_actual", 0)*60*c.get("tiempo", 0))*100 + c.get("mejora_propuesta", 0)) if c.get("bpm_actual", 0) and c.get("tiempo", 0) else 0 for c in captures) / n,
        "std_pt": sum(((c.get("peso_gr", 0)/1000)*c.get("bpm_actual", 0)*60)*c.get("eff_std_empaque", 0)/100 for c in captures) / n,
        "actual_pt": sum(((c.get("peso_gr", 0)/1000)*c.get("bpm_actual", 0)*60)*(safe_div(c.get("total_pq_buenos", 0), c.get("bpm_actual", 0)*60*c.get("tiempo", 0))*100)/100 if c.get("bpm_actual", 0) and c.get("tiempo", 0) else 0 for c in captures) / n,
        "propuesta_pt": sum(((c.get("peso_gr", 0)/1000)*c.get("bpm_propuesta", 0)*60)*((safe_div(c.get("total_pq_buenos", 0), c.get("bpm_actual", 0)*60*c.get("tiempo", 0))*100) + c.get("mejora_propuesta", 0))/100 if c.get("bpm_actual", 0) and c.get("tiempo", 0) else 0 for c in captures) / n,
        "global_pt": sum(((c.get("peso_gr", 0)/1000)*c.get("bpm_global", 0)*60)*c.get("eff_std_empaque", 0)/100 for c in captures) / n,
        "desperdicio": sum(c.get("total_pq", 0) - c.get("total_pq_buenos", 0) for c in captures) / n,
    }

@app.route('/eff_empaque/<int:exercise_id>/excel', methods=['GET', 'POST'])
def excel_eff_empaque(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data) if exercise.data else {"captures": []}
    if "captures" not in data:
        data = {"captures": [data]}
    flavors = Flavor.query.filter_by(bu_id=exercise.bu_id).all()
    plants = Plant.query.all()

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
    averages = calcular_promedios(data["captures"])
    flavors = Flavor.query.filter_by(bu_id=exercise.bu_id).all()
    return render_template('excel_eff_empaque.html', exercise=exercise, data=data, flavors=flavors, plants=plants, averages=averages)

# ===================== RUTAS PARA EL EJERCICIO "DME" (DEFECT MONITORING EXERCISE) =====================

@app.route('/dme_exercises', methods=['GET'])
def dme_exercises():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    query = request.args.get('q', '')
    exercises = DmeExercise.query.order_by(DmeExercise.created_at.desc()).all()
    
    # Procesar los datos para contar defectos
    for exercise in exercises:
        data = json.loads(exercise.data)
        # Asegurarse de que siempre haya una lista de capturas
        if "capturas" not in data or not isinstance(data["capturas"], list):
            data["capturas"] = []
            exercise.data = json.dumps(data)
            db.session.commit()
    
    bus = BusinessUnit.query.all()
    plants = Plant.query.all()
    return render_template('dme_exercises.html', exercises=exercises, query=query, bus=bus, plants=plants)

@app.route('/dme_exercises/new', methods=['GET', 'POST'])
def new_dme_exercise():
    if 'user_id' not in session:
        flash("Debe iniciar sesión para crear un ejercicio")
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        # Mostrar el formulario para seleccionar BU, planta y línea
        bus = BusinessUnit.query.all()
        plants = Plant.query.all()
        
        # Preparar datos para el formulario
        plantas_por_bu = {}
        lineas_por_planta = {}
        
        for plant in plants:
            # Agrupar plantas por BU
            if plant.bu_id not in plantas_por_bu:
                plantas_por_bu[plant.bu_id] = []
            plantas_por_bu[plant.bu_id].append({
                'id': plant.id,
                'name': plant.name
            })
            
            # Agrupar líneas por planta
            lineas = []
            for linea in plant.lineas:
                lineas.append({
                    'id': linea.id,
                    'name': linea.name
                })
            lineas_por_planta[plant.id] = lineas
        # Convertir a JSON para usar en JavaScript
        plantas_json = json.dumps(plantas_por_bu)
        lineas_json = json.dumps(lineas_por_planta)
        
        return render_template('new_dme_exercise.html', bus=bus, plants=plants, 
                               plantas_json=plantas_json, lineas_json=lineas_json)
    
    # Si es POST, procesamos la creación del ejercicio
    bu_id = request.form.get('bu_id')
    plant_id = request.form.get('plant_id')
    linea = request.form.get('linea')
    
    if not bu_id or not plant_id or not linea:
        flash("Debe seleccionar BU, Planta y Línea")
        return redirect(url_for('dme_exercises'))
    
    default_data = {
        "capturas": []
    }
    
    try:
        exercise = DmeExercise(bu_id=bu_id, plant_id=plant_id, linea=linea, data=json.dumps(default_data))
        db.session.add(exercise)
        db.session.commit()
        flash("Ejercicio DME creado exitosamente")
        return redirect(url_for('view_dme_exercise', exercise_id=exercise.id))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear el ejercicio: {str(e)}")
        return redirect(url_for('dme_exercises'))

@app.route('/dme_exercises/<int:exercise_id>/view', methods=['GET'])
def view_dme_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    return render_template('dme_exercise_detail.html', exercise=exercise, data=data)

@app.route('/dme_exercises/<int:exercise_id>/new_capture', methods=['GET', 'POST'])
def new_dme_capture(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    # Obtener la línea y su cantidad de pipes
    linea_obj = Line.query.filter_by(name=exercise.linea, plant_id=exercise.plant_id).first()
    pipes = linea_obj.pipes if linea_obj else 0

    if request.method == 'GET':
        return render_template('new_dme_capture.html', exercise=exercise, pipes=pipes)
    
    # Si es POST, procesamos la nueva captura
    maquina = request.form.get('maquina')
    
    if not maquina:
        flash("Debe ingresar el nombre de la máquina")
        return redirect(url_for('view_dme_exercise', exercise_id=exercise_id))
    
    # Cargar datos existentes
    data = json.loads(exercise.data)
    
    # Crear nueva captura
    nueva_captura = {
        "id": str(datetime.now().timestamp()),
        "maquina": maquina,
        "fecha_hora": datetime.now().isoformat(),
        "defectos": [],
        "bolsas_reales": 0
    }
    
    # Agregar la nueva captura a los datos existentes
    if "capturas" not in data:
        data["capturas"] = []
    
    data["capturas"].append(nueva_captura)
    
    # Actualizar el ejercicio
    exercise.data = json.dumps(data)
    exercise.updated_at = datetime.now()
    
    try:
        db.session.commit()
        flash("Captura creada exitosamente")
        return redirect(url_for('view_dme_capture', exercise_id=exercise_id, capture_id=nueva_captura["id"]))
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear la captura: {str(e)}")
        return redirect(url_for('view_dme_exercise', exercise_id=exercise_id))

@app.route('/dme_exercises/<int:exercise_id>/captures/<capture_id>', methods=['GET'])
def view_dme_capture(exercise_id, capture_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    
    # Buscar la captura específica
    captura = None
    for c in data.get("capturas", []):
        if c["id"] == capture_id:
            captura = c
            break
    
    if not captura:
        flash("Captura no encontrada")
        return redirect(url_for('view_dme_exercise', exercise_id=exercise_id))
    
    # Lista de tipos de defectos disponibles
    defect_types = [
        "Arranque de maquina (al principio)", "Sello vertical debil", "Arrugas en plancha (por quemado)",
        "Pliegues en plancha (capilares)", "Bolsas por cambio de bobina", "Producto atrapado por mordaza",
        "Arrugas mordaza (por quemado)", "Pliegues en mordaza", "Sello de mordaza debil",
        "Exceso de presión en mordaza", "Esquina de mordaza quemadas", "Codigo incorrecto",
        "Marcas de formador", "Bolsa vacia", "Defecto por tira promocional",
        "Atrapamiento de promocion", "Pinhole", "Bolsas explotadas",
        "Impresión fuera de registro", "Impresión defasada", "Bolsas tiznadas",
        "Baja cama de aire", "Detector de metal", "Bolsa rasgada",
        "Bolsa en tubo (desplazamiento de film)", "Bolsas explotadas banda jirafa", "Bolsas por datos de calidad",
        "Sobrecarga de producto", "Bajo gramaje", "Atora miento producto",
        "Prueba nitrógeno", "Empalme (cinta roja)", "Bolsa pegada en bobina",
        "Traslape incorrecto", "Otro (especificar en comentarios)"
    ]
    
    return render_template('dme_capture_detail.html', exercise=exercise, captura=captura, defect_types=defect_types)

@app.route('/dme_exercises/<int:exercise_id>/captures/<capture_id>/add_defect', methods=['POST'])
def add_dme_defect(exercise_id, capture_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    
    tipo_defecto = request.form.get('tipo_defecto')
    cantidad = request.form.get('cantidad', 1, type=int)
    comentario = request.form.get('comentario', '')
    
    if not tipo_defecto:
        flash("Debe seleccionar un tipo de defecto")
        return redirect(url_for('view_dme_capture', exercise_id=exercise_id, capture_id=capture_id))
    
    # Buscar la captura
    capture_index = None
    for i, c in enumerate(data.get("capturas", [])):
        if c["id"] == capture_id:
            capture_index = i
            break
    
    if capture_index is None:
        flash("Captura no encontrada")
        return redirect(url_for('view_dme_exercise', exercise_id=exercise_id))
    
    # Procesar imagen si existe
    imagen_url = None
    if 'imagen' in request.files and request.files['imagen'].filename:
        imagen = request.files['imagen']
        if allowed_file(imagen.filename):
            # Generar nombre de archivo único
            filename = secure_filename(imagen.filename)
            # Añadir timestamp para evitar nombres duplicados
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            # Guardar archivo
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagen.save(filepath)
            # Guardar URL relativa para acceso web
            imagen_url = f"/static/uploads/{filename}"
    
    # Calcular la hora relativa desde el inicio del ejercicio
    hora_inicio = datetime.fromisoformat(data["capturas"][capture_index]["fecha_hora"])
    hora_actual = datetime.now()
    diferencia_horas = int((hora_actual - hora_inicio).total_seconds() / 3600)
    
    hora_captura = request.form.get('hora_captura', type=int)
    if hora_captura and 1 <= hora_captura <= 24:
        hora_relativa = f"Hora {hora_captura}"
    else:
        # Si no se envía, calcular como antes
        hora_inicio = datetime.fromisoformat(data["capturas"][capture_index]["fecha_hora"])
        hora_actual = datetime.now()
        diferencia_horas = int((hora_actual - hora_inicio).total_seconds() / 3600)
        hora_relativa = f"Hora {diferencia_horas}"

    # Crear nuevo defecto
    nuevo_defecto = {
        "id": str(datetime.now().timestamp()),
        "tipo": tipo_defecto,
        "cantidad": cantidad,
        "comentario": comentario,
        "fecha_hora": datetime.now().isoformat(),
        "hora_relativa": hora_relativa,
        "imagen": imagen_url
    }
    
    # Agregar el defecto a la captura
    data["capturas"][capture_index]["defectos"].append(nuevo_defecto)
    
    # Actualizar el ejercicio
    exercise.data = json.dumps(data)
    exercise.updated_at = datetime.now()
    
    try:
        db.session.commit()
        flash("Defecto agregado exitosamente")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al agregar el defecto: {str(e)}")
    
    return redirect(url_for('view_dme_capture', exercise_id=exercise_id, capture_id=capture_id))

@app.route('/dme_exercises/<int:exercise_id>/delete', methods=['POST'])
def delete_dme_exercise(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    
    try:
        db.session.delete(exercise)
        db.session.commit()
        flash("Ejercicio DME eliminado exitosamente")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el ejercicio: {str(e)}")
    
    return redirect(url_for('dme_exercises'))

@app.route('/dme_exercises/<int:exercise_id>/captures/<capture_id>/delete_defect/<defect_id>', methods=['POST'])
def delete_dme_defect(exercise_id, capture_id, defect_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    
    # Buscar la captura y el defecto
    for i, captura in enumerate(data.get("capturas", [])):
        if captura["id"] == capture_id:
            for j, defecto in enumerate(captura.get("defectos", [])):
                if defecto["id"] == defect_id:
                    # Eliminar el defecto
                    data["capturas"][i]["defectos"].pop(j)
                    
                    # Actualizar el ejercicio
                    exercise.data = json.dumps(data)
                    exercise.updated_at = datetime.now()
                    
                    try:
                        db.session.commit()
                        flash("Defecto eliminado exitosamente")
                    except Exception as e:
                        db.session.rollback()
                        flash(f"Error al eliminar el defecto: {str(e)}")
                    
                    return redirect(url_for('view_dme_capture', exercise_id=exercise_id, capture_id=capture_id))
    
    flash("Defecto no encontrado")
    return redirect(url_for('view_dme_capture', exercise_id=exercise_id, capture_id=capture_id))

@app.route('/dme_exercises/<int:exercise_id>/edit_name', methods=['POST'])
def edit_dme_name(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    exercise = DmeExercise.query.get_or_404(exercise_id)
    nombre = request.form.get('nombre', '').strip()
    exercise.nombre = nombre
    exercise.updated_at = datetime.now()
    db.session.commit()
    flash("Nombre del DME actualizado")
    return redirect(url_for('dme_exercises'))

# ===================== RUTAS PARA DME AGRUPADO POR HORAS =====================

@app.route('/dme_exercises/<int:exercise_id>/captures', methods=['GET'])
def view_dme_captures(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    
    # Agrupar capturas por hora relativa
    capturas_por_hora = {}
    total_defectos = 0
    
    for captura in data.get("capturas", []):
        # Calcular la hora relativa basada en la fecha de creación del ejercicio
        fecha_ejercicio = exercise.created_at
        fecha_captura = datetime.fromisoformat(captura.get("fecha_hora", datetime.now().isoformat()))
        
        diferencia_horas = int((fecha_captura - fecha_ejercicio).total_seconds() / 3600)
        hora_clave = f"Hora {diferencia_horas}"
        
        # Inicializar la hora si no existe
        if hora_clave not in capturas_por_hora:
            capturas_por_hora[hora_clave] = {
                "capturas": [],
                "total_defectos": 0,
                "bolsas_reales": captura.get("bolsas_reales", 0)
            }
        
        # Añadir la captura al grupo correspondiente
        capturas_por_hora[hora_clave]["capturas"].append(captura)
        
        # Sumar defectos
        defectos_en_captura = len(captura.get("defectos", []))
        capturas_por_hora[hora_clave]["total_defectos"] += defectos_en_captura
        total_defectos += defectos_en_captura
    
    # Ordenar las horas
    horas_ordenadas = sorted(capturas_por_hora.keys(), key=lambda x: int(x.split(" ")[1]))
    
    return render_template('dme_captures.html', 
                           exercise=exercise, 
                           capturas_por_hora=capturas_por_hora,
                           horas_ordenadas=horas_ordenadas,
                           total_defectos=total_defectos)

@app.route('/dme_exercises/<int:exercise_id>/update_bolsas_reales', methods=['POST'])
def update_bolsas_reales(exercise_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    
    hora = request.form.get('hora')
    bolsas_reales = request.form.get('bolsas_reales', 0, type=int)
    
    # Actualizar todas las capturas de esa hora con el valor de bolsas reales
    fecha_ejercicio = exercise.created_at
    
    for captura in data.get("capturas", []):
        fecha_captura = datetime.fromisoformat(captura.get("fecha_hora", datetime.now().isoformat()))
        diferencia_horas = int((fecha_captura - fecha_ejercicio).total_seconds() / 3600)
        hora_captura = f"Hora {diferencia_horas}"
        
        if hora_captura == hora:
            captura["bolsas_reales"] = bolsas_reales
    
    # Guardar los cambios
    exercise.data = json.dumps(data)
    db.session.commit()
    
    flash(f"Bolsas reales actualizadas para {hora}")
    return redirect(url_for('view_dme_captures', exercise_id=exercise_id))

@app.route('/eff_empaque/<int:exercise_id>/update_mejora_propuesta', methods=['POST'])
def update_mejora_propuesta(exercise_id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado"), 401
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data) if exercise.data else {"captures": []}
    req = request.get_json()
    index = int(req.get('index', -1))
    value = req.get('value')
    try:
        value = float(value)
    except Exception:
        return jsonify(success=False, message="Valor inválido"), 400
    if 0 <= index < len(data.get("captures", [])):
        data["captures"][index]["mejora_propuesta"] = value
        exercise.data = json.dumps(data)
        exercise.updated_at = datetime.now()
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Índice fuera de rango"), 400

@app.route('/eff_empaque/<int:exercise_id>/delete_capture', methods=['POST'])
def delete_capture_eff_empaque(exercise_id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado"), 401
    exercise = EmpaqueExercise.query.get_or_404(exercise_id)
    import json
    data = json.loads(exercise.data) if exercise.data else {"captures": []}
    req = request.get_json()
    index = int(req.get('index', -1))
    if 0 <= index < len(data.get("captures", [])):
        data["captures"].pop(index)
        exercise.data = json.dumps(data)
        exercise.updated_at = datetime.now()
        db.session.commit()
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="Índice fuera de rango"), 400

@app.route('/dme_exercises/<int:exercise_id>/captures/<capture_id>/delete', methods=['POST'])
def delete_dme_capture(exercise_id, capture_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    exercise = DmeExercise.query.get_or_404(exercise_id)
    import json
    data = json.loads(exercise.data)
    # Buscar y eliminar la captura
    capturas = data.get("capturas", [])
    nueva_lista = [c for c in capturas if str(c.get("id")) != str(capture_id)]
    if len(nueva_lista) == len(capturas):
        flash("Captura no encontrada")
    else:
        data["capturas"] = nueva_lista
        exercise.data = json.dumps(data)
        exercise.updated_at = datetime.now()
        try:
            db.session.commit()
            flash("Captura eliminada exitosamente")
        except Exception as e:
            db.session.rollback()
            flash(f"Error al eliminar la captura: {str(e)}")
    return redirect(url_for('view_dme_exercise', exercise_id=exercise_id))

@app.route('/dme_exercises/<int:exercise_id>/captures/<capture_id>/update_cantidad', methods=['POST'])
def update_dme_defecto_cantidad(exercise_id, capture_id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado"), 401
    exercise = DmeExercise.query.get_or_404(exercise_id)
    data = json.loads(exercise.data)
    req = request.get_json()
    defecto_id = req.get('defecto_id')
    cantidad = req.get('cantidad')
    try:
        cantidad = int(cantidad)
    except Exception:
        return jsonify(success=False, message="Cantidad inválida"), 400

    for captura in data.get("capturas", []):
        if str(captura.get("id")) == str(capture_id):
            for defecto in captura.get("defectos", []):
                if str(defecto.get("id")) == str(defecto_id):
                    defecto["cantidad"] = cantidad
                    exercise.data = json.dumps(data)
                    exercise.updated_at = datetime.now()
                    db.session.commit()
                    return jsonify(success=True)
    return jsonify(success=False, message="Defecto no encontrado"), 404

@app.route('/pesos')
def pesos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ejercicios = PesoRegistro.query.order_by(PesoRegistro.fecha.desc()).all()
    lineas = Line.query.all()
    plantas = Plant.query.all()
    bus = BusinessUnit.query.all()
    return render_template('pesos.html', ejercicios=ejercicios, query=request.args.get('q', ''), lineas=lineas, plantas=plantas, bus=bus)

@app.route('/pesos/new', methods=['POST'])
def new_peso_ejercicio():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nombre = request.form.get('nombre')
    linea_id = request.form.get('linea_id')
    plant_id = request.form.get('plant_id')
    bu_id = request.form.get('bu_id')

    if not linea_id or not plant_id or not bu_id:
        flash("Debe seleccionar BU, Planta y Línea", "danger")
        return redirect(url_for('pesos'))

    nuevo = PesoRegistro(nombre=nombre, linea_id=linea_id, fecha=datetime.now())
    db.session.add(nuevo)
    db.session.commit()
    flash("Ejercicio de peso creado correctamente", "success")
    return redirect(url_for('pesos'))

@app.route('/eliminar_registro_peso/<int:id>', methods=['POST'])
def eliminar_registro_peso(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    registro = PesoRegistro.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    flash("Ejercicio eliminado", "success")
    return redirect(url_for('pesos'))

@app.route('/pesos_detail', methods=['GET', 'POST'])
def pesos_detail():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ejercicio_id = request.args.get('id', type=int)
    ejercicio = PesoRegistro.query.get(ejercicio_id) if ejercicio_id else None
    sabores = Flavor.query.all()
    if request.method == 'POST':
        sabor_id = request.form.get('producto_id')
        turno = request.form.get('turno')
        maquina = request.form.get('maquina_id')
        peso_fijado = request.form.get('peso_fijado', type=float)
        limite_superior = request.form.get('limite_superior', type=float)
        control_promedio = request.form.get('control_promedio')
        compensacion = request.form.get('compensacion', type=float)
        intervalo_auto_cero = request.form.get('intervalo_auto_cero', type=int)
        numero_estable = request.form.get('numero_estable', type=int)
        usuario = session.get('username', 'desconocido')

        registro = PesoRegistro(
            sabor_id=sabor_id,
            turno=turno,
            maquina=maquina,
            peso_fijado=peso_fijado,
            limite_superior=limite_superior,
            control_promedio=control_promedio,
            compensacion=compensacion,
            intervalo_auto_cero=intervalo_auto_cero,
            numero_estable=numero_estable,
            usuario=usuario,
        )
        db.session.add(registro)
        db.session.commit()
        flash("Registro de peso guardado correctamente", "success")
        return redirect(url_for('pesos_detail'))

    return render_template('pesos_detail.html', ejercicio=ejercicio, productos=sabores, maquinas=[], session=session)

@app.route('/editar_registro_peso/<int:id>', methods=['GET', 'POST'])
def editar_registro_peso(id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado")
    registro = PesoRegistro.query.get_or_404(id)
    if request.method == 'POST':
        data = request.json
        registro.turno = data.get('turno')
        registro.sabor_id = data.get('producto_id')
        registro.maquina = data.get('maquina_id')
        registro.peso_fijado = data.get('peso_fijado', 0)
        registro.limite_superior = data.get('limite_superior', 0)
        registro.control_promedio = data.get('control_promedio')
        registro.compensacion = data.get('compensacion', 0)
        registro.intervalo_auto_cero = data.get('intervalo_auto_cero', 0)
        registro.numero_estable = data.get('numero_estable', 0)
        db.session.commit()
        return jsonify(success=True)
    # GET: devolver datos del registro
    return jsonify(
        id=registro.id,
        turno=registro.turno,
        producto_id=registro.sabor_id,
        maquina_id=registro.maquina,
        peso_fijado=registro.peso_fijado,
        limite_superior=registro.limite_superior,
        control_promedio=registro.control_promedio,
        compensacion=registro.compensacion,
        intervalo_auto_cero=registro.intervalo_auto_cero,
        numero_estable=registro.numero_estable
    )

@app.route('/obtener_pesos_individuales/<int:id>', methods=['GET'])
def obtener_pesos_individuales(id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado"), 401
    registro = PesoRegistro.query.get_or_404(id)
    try:
        data = json.loads(registro.data) if registro.data else {}
    except Exception:
        data = {}
    cantidad = data.get('cantidad_pesos', 1)
    pesos = data.get('pesos', [])
    return jsonify(success=True, cantidad=cantidad, pesos=pesos)

@app.route('/guardar_pesos_individuales/<int:id>', methods=['POST'])
def guardar_pesos_individuales(id):
    if 'user_id' not in session:
        return jsonify(success=False, message="No autorizado"), 401
    registro = PesoRegistro.query.get_or_404(id)
    req = request.get_json()
    cantidad = req.get('cantidad', 1)
    pesos = req.get('pesos', [])
    # Guardar en el campo data como JSON
    try:
        data = json.loads(registro.data) if registro.data else {}
    except Exception:
        data = {}
    data['cantidad_pesos'] = cantidad
    data['pesos'] = pesos
    registro.data = json.dumps(data)
    db.session.commit()
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')
