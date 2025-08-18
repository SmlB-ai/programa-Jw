import calendar
from datetime import date
from .database.database_manager import get_db_connection, get_people_for_role, get_meeting_template

# --- Definición de Metadatos de Asignaciones (Claves Robustas) ---
# Las claves ahora coinciden exactamente con el texto de la plantilla para evitar errores.
# Esta estructura sigue siendo necesaria para mapear texto a requisitos.
ASSIGNMENT_METADATA = {
    'Presidente:': {'role': 'Presidente', 'gender': 'Hombre', 'count': 1},
    'Oracion de inicio:': {'role': 'Oración', 'gender': 'Hombre', 'count': 1},
    'Oracion de final:': {'role': 'Oración', 'gender': 'Hombre', 'count': 1},
    'Busquemos perlas escondidas': {'role': 'Anciano', 'gender': 'Hombre', 'count': 1},
    'Lectura de la Biblia': {'role': 'Lector', 'gender': 'Hombre', 'count': 1},
    'Lectura de la Biblia (Sala auxiliar B)': {'role': 'Lector', 'gender': 'Hombre', 'count': 1},
    'Estudio Biblico:': {'role': 'Estudio Bíblico Conductor', 'gender': 'Hombre', 'count': 1},
    'Lector:': {'role': 'Estudio Bíblico Lector', 'gender': 'Hombre', 'count': 1},

    # --- Asignaciones de la sala B y Seamos Mejores Maestros ---
    'Empiece conversaciones (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Haga discípulos  (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Haga revisitas  (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Explique sus creencias  (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Discurso  (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Haga revisitas (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Explique sus creencias (Sala auxiliar B)': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},

    'Empiece conversaciones': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Haga revisitas': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Haga discípulos': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Explique sus creencias': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},
    'Discurso': {'role': 'Siervo Ministerial', 'gender': 'Mujer', 'count': 2},

    'Acomodadores de entrada': {'role': 'Acomodador', 'gender': 'Cualquiera', 'count': 3},
    'Acomodadores de auditorio': {'role': 'Acomodador', 'gender': 'Cualquiera', 'count': 2}
}

# La plantilla hardcodeada (USER_TEMPLATE_STRUCTURE) se elimina de aquí.
# La primera vez se migrará a la BD desde database_setup.

def _get_metadata_for_slot(row_idx, col_idx, week_template):
    """Encuentra la metadata de una asignación basada en su posición en la plantilla."""
    if col_idx > 0 and week_template[row_idx][col_idx - 1]:
        key = week_template[row_idx][col_idx - 1]
    elif row_idx > 0 and week_template[row_idx - 1][col_idx] not in ('N', '/'):
        key = week_template[row_idx - 1][col_idx]
    else:
        return None

    # La búsqueda ahora es directa y más robusta
    return ASSIGNMENT_METADATA.get(key.strip())


def find_best_candidate(role, gender, slot_description, excluded_ids):
    candidates = get_people_for_role(role, gender)
    valid_candidates = [p for p in candidates if p['id'] not in excluded_ids]
    if not valid_candidates: return None, "NADIE DISPONIBLE"
    conn = get_db_connection()
    cursor = conn.cursor()
    candidate_last_assigned = {}
    for candidate in valid_candidates:
        cursor.execute("SELECT MAX(fecha_reunion) FROM asignaciones_historial WHERE persona_id = ? AND descripcion_asignacion = ?", (candidate['id'], slot_description))
        last_date = cursor.fetchone()[0]
        candidate_last_assigned[candidate['id']] = last_date or '1970-01-01'
    conn.close()
    sorted_candidate_ids = sorted(candidate_last_assigned.items(), key=lambda item: item[1])
    best_candidate_id = sorted_candidate_ids[0][0]
    for cand in valid_candidates:
        if cand['id'] == best_candidate_id: return cand['id'], cand['nombre']
    return None, "NO ENCONTRADO"

from .database.database_manager import get_special_weeks_for_month

def generate_schedule(year, month, meeting_day=calendar.THURSDAY):
    cal = calendar.Calendar()
    month_dates = [d for d in cal.itermonthdates(year, month) if d.weekday() == meeting_day and d.month == month]
    special_weeks = get_special_weeks_for_month(year, month)
    final_filled_template = []

    for week_idx, meeting_date in enumerate(month_dates):
        date_str = meeting_date.strftime("%Y-%m-%d")
        if date_str in special_weeks:
            final_filled_template.append({
                'is_special': True,
                'reason': special_weeks[date_str]
            })
            continue

        # Obtener la plantilla desde la base de datos
        week_type = week_idx % 4
        week_template = get_meeting_template(week_type)

        if not week_template:
            # Manejar el caso en que la plantilla no exista en la BD
            print(f"Error: No se encontró la plantilla para el tipo de semana {week_type}")
            # Podríamos añadir una semana vacía o con un mensaje de error
            final_filled_template.append([])
            continue

        filled_week = []
        assigned_ids_this_week = []

        for row_idx, row_data in enumerate(week_template):
            filled_row = list(row_data)
            for col_idx, cell_content in enumerate(row_data):
                if cell_content in ('N', '/'):
                    metadata = _get_metadata_for_slot(row_idx, col_idx, week_template)
                    if not metadata:
                        # Si no hay metadata, no es una asignación que debamos procesar
                        continue

                    # La clave para el historial es la que coincide en los metadatos
                    slot_key = list(ASSIGNMENT_METADATA.keys())[list(ASSIGNMENT_METADATA.values()).index(metadata)]

                    assignments = []
                    for i in range(metadata['count']):
                        person_id, person_name = find_best_candidate(
                            metadata['role'], metadata['gender'], slot_key, assigned_ids_this_week
                        )
                        if person_id:
                            assigned_ids_this_week.append(person_id)
                        assignments.append(person_name or "NO DISPONIBLE")

                    filled_row[col_idx] = " / ".join(assignments)

            filled_week.append(tuple(filled_row))
        final_filled_template.append(filled_week)

    return month_dates, final_filled_template
