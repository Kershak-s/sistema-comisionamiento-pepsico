# Agregar estas funciones a app.py

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