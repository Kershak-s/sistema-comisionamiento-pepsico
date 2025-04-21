# Sistema de Comisionamiento PepsiCo

## Descripción del Proyecto

El Sistema de Comisionamiento de PepsiCo es una aplicación web desarrollada para gestionar y optimizar los procesos de producción y empaque en las plantas de PepsiCo. La plataforma permite realizar seguimiento de eficiencia, analizar indicadores de desempeño y gestionar ejercicios de mejora en tiempo real.

### Características Principales

- **Gestión de Unidades de Negocio**: Administración centralizada de BUs, plantas, líneas y sabores.
- **Ejercicios de Eficiencia de Empaque**: Medición y análisis de eficiencia en líneas de producción.
- **Dashboard Analítico**: Visualización de KPIs y métricas de desempeño.
- **Sistema de Autenticación**: Control de acceso con roles diferenciados (administrador y usuario).
- **Análisis Deep Dive**: Herramientas para análisis detallado de indicadores operativos.

## Tecnologías Utilizadas

- **Backend**: 
  - Python 3.10
  - Flask 2.2.5
  - SQLAlchemy (ORM)
  - SQLite (Base de datos)

- **Frontend**:
  - HTML5, CSS3, JavaScript
  - Bootstrap 5
  - Jinja2 (Motor de plantillas)

## Estructura del Proyecto

```
sistema-comisionamiento/
├── app.py                 # Aplicación principal y rutas
├── models.py              # Modelos de datos y esquema de la BD
├── requirements.txt       # Dependencias del proyecto
├── instance/              # Base de datos SQLite
├── static/                # Archivos estáticos (CSS, JS, imágenes)
│   └── img/               # Imágenes del sistema
├── templates/             # Plantillas HTML
│   ├── admin_*.html       # Plantillas de administración
│   ├── eff_empaque_*.html # Plantillas para ejercicios de eficiencia
│   └── base.html          # Plantilla base
└── venv/                  # Entorno virtual (no incluido en repo)
```

## Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/Kershak-s/sistema-comisionamiento-pepsico.git
   cd sistema-comisionamiento-pepsico
   ```

2. **Crear y activar entorno virtual**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**
   ```bash
   python app.py
   ```

5. **Acceder a la aplicación**
   - Abrir navegador y visitar: `http://localhost:5000/`
   - Credenciales por defecto:
     - Usuario: `admin`
     - Contraseña: `PEPCODE`

## Módulos Principales

### Módulo de Administración

Permite a los administradores gestionar:
- Usuarios y permisos
- Unidades de negocio (BUs)
- Plantas de producción
- Líneas de producción
- Catálogo de sabores

### Módulo de Eficiencia de Empaque

Herramienta para el análisis de eficiencia en líneas de producción que permite:
- Crear ejercicios de medición
- Capturar datos de producción
- Calcular indicadores clave (BPM, eficiencia)
- Proponer mejoras y simular impacto

### Dashboard y Reporting

Visualización de métricas clave:
- Eficiencia por línea y planta
- Comparativo con estándares globales
- Oportunidades de mejora identificadas

## Uso del Sistema

### Gestión de Usuarios

1. Acceder como administrador
2. Navegar a la sección "Administrar Usuarios"
3. Crear, editar o eliminar usuarios según sea necesario

### Ejercicios de Eficiencia de Empaque

1. Desde el dashboard, seleccionar "Eficiencia de Empaque"
2. Crear un nuevo ejercicio seleccionando BU y planta
3. Completar el formulario con los datos de la línea de producción
4. Guardar y analizar los resultados de eficiencia

## Seguridad

- El sistema implementa autenticación de usuarios mediante Flask-Login
- Las contraseñas se almacenan con hash utilizando Werkzeug Security
- Roles diferenciados para controlar acceso a funcionalidades críticas

## Desarrollo y Contribución

### Convenciones de Código

- Seguir PEP 8 para Python
- Usar convención camelCase para JavaScript
- Comentar el código adecuadamente

### Flujo de Trabajo de Desarrollo

1. Crear una rama para cada nueva característica
2. Implementar y probar localmente
3. Solicitar revisión de código
4. Fusionar a la rama principal tras aprobación

## Mantenimiento y Soporte

Para reportar problemas o solicitar nuevas características, contactar:

- **Equipo de Desarrollo**: desarrollo@ejemplo.com
- **Soporte Técnico**: soporte@ejemplo.com

## Roadmap

Próximas funcionalidades planificadas:

- [ ] Integración con sistemas ERP
- [ ] Módulo de reportes avanzados
- [ ] Aplicación móvil para captura en planta
- [ ] Panel de análisis predictivo

## Licencia

Este software es propiedad de PepsiCo y su uso está restringido a personal autorizado.

Copyright © 2025 PepsiCo, Inc. Todos los derechos reservados.