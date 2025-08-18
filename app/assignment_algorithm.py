import calendar
from datetime import date
from .database.database_manager import get_db_connection, get_people_for_role

# --- Definición de Metadatos de Asignaciones (Claves Robustas) ---
# Las claves ahora coinciden exactamente con el texto de la plantilla para evitar errores.
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
    # Usamos la clave completa para evitar ambigüedad
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

# --- Plantilla Estructurada ---
USER_TEMPLATE_STRUCTURE = [
    # ... (la estructura de la plantilla no cambia)
]

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

def generate_schedule(year, month, meeting_day=calendar.THURSDAY):
    cal = calendar.Calendar()
    month_dates = [d for d in cal.itermonthdates(year, month) if d.weekday() == meeting_day and d.month == month]
    final_filled_template = []

    for week_idx, meeting_date in enumerate(month_dates):
        week_template = USER_TEMPLATE_STRUCTURE[week_idx % len(USER_TEMPLATE_STRUCTURE)]
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

# Re-pegar la plantilla completa para asegurar que está en el archivo
USER_TEMPLATE_STRUCTURE = [
    # Semana 1
    [("de 2025", "Presidente:"),("Oracion de inicio:", "Lectura de la Biblia (Sala auxiliar B)"),("TESOROS DE LA BIBLIA", "/"),("Padres sigan cuidando la herencia que Jehová les dio", "Empiece conversaciones (Sala auxiliar B)"),("N", "/"),("Busquemos perlas escondidas", "Empiece conversaciones (Sala auxiliar B)"),("N", "/"),("Lectura de la Biblia", "Haga discípulos  (Sala auxiliar B)"),("N", "/"),("SEAMOS MEJORES MAESTROS", "NUESTRA VIDA CRISTIANA"),("Empiece conversaciones", "Bosquejo"),("/", "N"),("Empiece conversaciones", ""),("/", "Estudio Biblico:"),("Haga discípulos", "Lector:"),("/", "N"),("", "Oracion de final:"),("Acomodadores de entrada", "Acomodadores de auditorio"),("N", "N"),],
    # Semana 2
    [(" de 2025", "Presidente:"),("Oracion de inicio:", "Lectura de la Biblia (Sala auxiliar B)"),("TESOROS DE LA BIBLIA", "/"),("Nuestro Señor es más grande que todos los demas dioses", "Empiece conversaciones (Sala auxiliar B)"),("N", "/"),("Busquemos perlas escondidas", "Haga revisitas  (Sala auxiliar B)"),("N", "/"),("Lectura de la Biblia", "Explique sus creencias  (Sala auxiliar B)"),("N", "/"),("SEAMOS MEJores MAESTROS", "NUESTRA VIDA CRISTIANA"),("Empiece conversaciones", "Necesidades de la congregación"),("/", "N"),("Haga revisitas", ""),("/", "Estudio Biblico:"),("Explique sus creencias", "Lector:"),("/", "N"),("", "Oracion de final:"),("Acomodadores de entrada", "Acomodadores de auditorio"),("N", "N"),],
    # Semana 3
    [("de 2025", "Presidente:"),("Oracion de inicio:", "Lectura de la Biblia (Sala auxiliar B)"),("TESOROS DE LA BIBLIA", "/"),("¡Que los nervios no lo frenen!", "Empiece conversaciones (Sala auxiliar B)"),("N", "/"),("Busquemos perlas escondidas", "Haga discípulos  (Sala auxiliar B)"),("N", "/"),("Lectura de la Biblia", "Discurso  (Sala auxiliar B)"),("N", "/"),("SEAMOS MEJORES MAESTROS", "NUESTRA VIDA CRISTIANA"),("Empiece conversaciones", "Bosquejo"),("/", "N"),("Haga discípulos", ""),("/", "Estudio Biblico:"),("Discurso", "Lector:"),("/", "N"),("", "Oracion de final:"),("Acomodadores de entrada", "Acomodadores de auditorio"),("N", "N"),],
    # Semana 4
    [("de 2025", "Presidente:"),("Oracion de inicio:", "Lectura de la Biblia (Sala auxiliar B)"),("TESOROS DE LA BIBLIA", "/"),("¿Qué hará despues de orar?", "Empiece conversaciones (Sala auxiliar B)"),("N", "/"),("Busquemos perlas escondidas", "Haga revisitas (Sala auxiliar B)"),("N", "/"),("Lectura de la Biblia", "Explique sus creencias (Sala auxiliar B)"),("N", "/"),("SEAMOS MEJORES MAESTROS", "NUESTRA VIDA CRISTIANA"),("Empiece conversaciones", "Bosquejo"),("/", ""),("Haga revisitas", "N"),("/", "Estudio Biblico:"),("Explique sus creencias", "Lector:"),("/", "N"),("", "Oracion de final:"),("Acomodadores de entrada", "Acomodadores de auditorio"),("N", "N"),]
]
