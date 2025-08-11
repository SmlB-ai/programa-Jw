import calendar
from datetime import date
from .database.database_manager import get_db_connection

# --- Definición de Plantillas Semanales ---
# Mapeo de descripción de la asignación al rol requerido en la BD.
# `None` para títulos o temas que no se asignan.

BASE_ASSIGNMENTS = [
    {'slot': 'Presidente', 'role': 'Presidente'},
    {'slot': 'Oracion de inicio', 'role': 'Oración'},
    # TESOROS
    {'slot': 'Busquemos perlas escondidas', 'role': 'Anciano'},
    {'slot': 'Lectura de la Biblia', 'role': 'Lector'},
    # VIDA CRISTIANA
    {'slot': 'Estudio Biblico: Conductor', 'role': 'Estudio Bíblico Conductor'},
    {'slot': 'Estudio Biblico: Lector', 'role': 'Estudio Bíblico Lector'},
    {'slot': 'Oracion de final', 'role': 'Oración'},
    {'slot': 'Acomodadores de entrada', 'role': 'Acomodador'},
    {'slot': 'Acomodadores de auditorio', 'role': 'Acomodador'},
]

# Plantillas específicas para cada semana del mes
TEMPLATE_WEEK_1 = [
    *BASE_ASSIGNMENTS,
    {'slot': 'Tesoros: Discurso', 'role': None, 'title': 'Padres sigan cuidando la herencia que Jehová les dio'},
    {'slot': 'Maestros: Empiece conversaciones', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Haga discípulos', 'role': 'Siervo Ministerial'},
    {'slot': 'Vida Cristiana: Tema', 'role': None, 'title': 'Bosquejo'},
]

TEMPLATE_WEEK_2 = [
    *BASE_ASSIGNMENTS,
    {'slot': 'Tesoros: Discurso', 'role': None, 'title': 'Nuestro Señor es más grande que todos los demas dioses'},
    {'slot': 'Maestros: Empiece conversaciones', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Haga revisitas', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Explique sus creencias', 'role': 'Siervo Ministerial'},
    {'slot': 'Vida Cristiana: Tema', 'role': None, 'title': 'Necesidades de la congregación'},
]

TEMPLATE_WEEK_3 = [
    *BASE_ASSIGNMENTS,
    {'slot': 'Tesoros: Discurso', 'role': None, 'title': '¡Que los nervios no lo frenen!'},
    {'slot': 'Maestros: Empiece conversaciones', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Haga discípulos', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Discurso', 'role': 'Siervo Ministerial'},
    {'slot': 'Vida Cristiana: Tema', 'role': None, 'title': 'Bosquejo'},
]

TEMPLATE_WEEK_4 = [
    *BASE_ASSIGNMENTS,
    {'slot': 'Tesoros: Discurso', 'role': None, 'title': '¿Qué hará despues de orar?'},
    {'slot': 'Maestros: Empiece conversaciones', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Haga revisitas', 'role': 'Siervo Ministerial'},
    {'slot': 'Maestros: Explique sus creencias', 'role': 'Siervo Ministerial'},
    {'slot': 'Vida Cristiana: Tema', 'role': None, 'title': 'Bosquejo'},
]

# Ciclo de plantillas
TEMPLATES_CYCLE = [TEMPLATE_WEEK_1, TEMPLATE_WEEK_2, TEMPLATE_WEEK_3, TEMPLATE_WEEK_4]

def find_best_candidate(role_name, slot_description, excluded_ids):
    """
    Encuentra el mejor candidato para un rol y una asignación específica,
    priorizando a quien no ha sido asignado en más tiempo para esa misma tarea.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Obtener todos los candidatos con el rol requerido que no estén excluidos
    query = "SELECT p.id, p.nombre FROM personas p JOIN personas_roles pr ON p.id = pr.persona_id JOIN roles r ON pr.rol_id = r.id WHERE r.nombre = ?"
    params = [role_name]
    if excluded_ids:
        placeholders = ','.join('?' for _ in excluded_ids)
        query += f" AND p.id NOT IN ({placeholders})"
        params.extend(excluded_ids)

    cursor.execute(query, params)
    candidates = cursor.fetchall()

    if not candidates:
        conn.close()
        return None, "NADIE DISPONIBLE"

    # 2. Para cada candidato, encontrar la fecha de su última asignación para este SLOT específico
    candidate_last_assigned = {}
    for candidate in candidates:
        cursor.execute(
            "SELECT MAX(fecha_reunion) FROM asignaciones_historial WHERE persona_id = ? AND descripcion_asignacion = ?",
            (candidate['id'], slot_description)
        )
        last_date = cursor.fetchone()[0]
        # Usar una fecha muy antigua si nunca ha sido asignado para priorizarlo
        candidate_last_assigned[candidate['id']] = last_date or '1970-01-01'

    conn.close()

    # 3. Ordenar los candidatos por la fecha de última asignación (el más antiguo primero)
    sorted_candidate_ids = sorted(candidate_last_assigned.items(), key=lambda item: item[1])
    best_candidate_id = sorted_candidate_ids[0][0]

    # Encontrar el nombre del mejor candidato
    for cand in candidates:
        if cand['id'] == best_candidate_id:
            return cand['id'], cand['nombre']

    return None, "NO ENCONTRADO"

def generate_schedule(year, month, meeting_day=calendar.THURSDAY):
    """
    Genera el horario completo para un mes y año dados, ciclando a través de las plantillas semanales.
    """
    cal = calendar.Calendar()
    # Obtener todas las fechas del día de la reunión (ej. jueves) en el mes
    month_dates = [d for d in cal.itermonthdates(year, month) if d.weekday() == meeting_day and d.month == month]

    full_schedule = {}
    template_idx = 0

    for meeting_date in month_dates:
        template = TEMPLATES_CYCLE[template_idx % len(TEMPLATES_CYCLE)]
        template_idx += 1

        date_str = meeting_date.strftime("%Y-%m-%d")
        weekly_schedule = {}
        assigned_ids_this_week = []

        for assignment in sorted(template, key=lambda x: x['slot']): # Ordenar para consistencia
            slot_name = assignment['slot']
            role_name = assignment.get('role')

            if role_name is None:
                weekly_schedule[slot_name] = assignment.get('title', '---')
                continue

            person_id, person_name = find_best_candidate(role_name, slot_name, assigned_ids_this_week)

            weekly_schedule[slot_name] = person_name

            if person_id is not None:
                assigned_ids_this_week.append(person_id)

        full_schedule[date_str] = weekly_schedule

    return full_schedule

# --- Ejemplo de uso (para pruebas) ---
if __name__ == '__main__':
    print("Módulo de algoritmo de asignación. Se necesita una base de datos poblada para probar.")
    # Para probar esto, se necesitaría ejecutarlo desde un contexto donde la BD esté poblada.
    # Por ejemplo:
    # from database_setup import setup_database
    # from database_manager import add_person_with_roles
    # setup_database()
    # add_person_with_roles("Juan Perez", [1, 3]) # Anciano, Lector
    # add_person_with_roles("Pedro Gomez", [2, 4]) # SM, Acomodador
    # schedule = generate_schedule(2025, 1)
    # import json
    # print(json.dumps(schedule, indent=2, ensure_ascii=False))
