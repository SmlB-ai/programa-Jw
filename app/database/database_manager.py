import sqlite3
import os

DB_FILE = "asignaciones.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_FILE)

def get_db_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_roles():
    """Obtiene todos los roles de la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM roles ORDER BY nombre")
    roles = cursor.fetchall()
    conn.close()
    return roles

def get_all_people_with_roles(role_id_filter=None):
    """
    Obtiene todas las personas con su género y roles asociados.
    Si se proporciona un role_id_filter, solo devuelve personas con ese rol.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    params = []
    if role_id_filter:
        query = """
        SELECT p.id, p.nombre, p.genero, GROUP_CONCAT(r.nombre, ', ') as roles
        FROM personas p
        LEFT JOIN personas_roles pr ON p.id = pr.persona_id
        LEFT JOIN roles r ON pr.rol_id = r.id
        JOIN personas_roles pr_filter ON p.id = pr_filter.persona_id
        WHERE pr_filter.rol_id = ?
        GROUP BY p.id
        ORDER BY p.nombre
        """
        params.append(role_id_filter)
    else:
        query = """
        SELECT p.id, p.nombre, p.genero, GROUP_CONCAT(r.nombre, ', ') as roles
        FROM personas p
        LEFT JOIN personas_roles pr ON p.id = pr.persona_id
        LEFT JOIN roles r ON pr.rol_id = r.id
        GROUP BY p.id
        ORDER BY p.nombre
        """

    cursor.execute(query, params)
    people = cursor.fetchall()
    conn.close()
    return people

def add_person_with_roles(nombre, genero, rol_ids):
    """Añade una nueva persona con su género y le asigna roles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO personas (nombre, genero) VALUES (?, ?)", (nombre, genero))
        persona_id = cursor.lastrowid
        if rol_ids:
            asignaciones = [(persona_id, rol_id) for rol_id in rol_ids]
            cursor.executemany("INSERT INTO personas_roles (persona_id, rol_id) VALUES (?, ?)", asignaciones)
        conn.commit()
    except sqlite3.IntegrityError:
        # El nombre de la persona ya existe
        conn.rollback()
        return None
    finally:
        conn.close()
    return persona_id

def update_person_with_roles(persona_id, nombre, genero, rol_ids):
    """Actualiza el nombre, género y roles de una persona."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Actualizar nombre y genero
        cursor.execute("UPDATE personas SET nombre = ?, genero = ? WHERE id = ?", (nombre, genero, persona_id))

        # Actualizar roles (borrar los antiguos e insertar los nuevos)
        cursor.execute("DELETE FROM personas_roles WHERE persona_id = ?", (persona_id,))
        if rol_ids:
            asignaciones = [(persona_id, rol_id) for rol_id in rol_ids]
            cursor.executemany("INSERT INTO personas_roles (persona_id, rol_id) VALUES (?, ?)", asignaciones)

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al actualizar: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_person(persona_id):
    """Elimina una persona de la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # La eliminación en cascada se encargará de las tablas relacionadas
        cursor.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error al eliminar: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_person_details(persona_id):
    """Obtiene los detalles de una persona, incluyendo su género y IDs de rol."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener nombre y genero
    cursor.execute("SELECT nombre, genero FROM personas WHERE id = ?", (persona_id,))
    persona = cursor.fetchone()
    if not persona:
        conn.close()
        return None, None, None

    # Obtener roles
    cursor.execute("SELECT rol_id FROM personas_roles WHERE persona_id = ?", (persona_id,))
    rol_ids = [row['rol_id'] for row in cursor.fetchall()]

    conn.close()
    return persona['nombre'], persona['genero'], rol_ids

def get_people_for_role(role_name, gender=None):
    """Obtiene todas las personas que tienen un rol y, opcionalmente, un género específico."""
    conn = get_db_connection()
    cursor = conn.cursor()

    params = [role_name]
    query = """
    SELECT p.id, p.nombre, p.genero
    FROM personas p
    JOIN personas_roles pr ON p.id = pr.persona_id
    JOIN roles r ON pr.rol_id = r.id
    WHERE r.nombre = ?
    """

    if gender and gender != 'Cualquiera':
        query += " AND p.genero = ?"
        params.append(gender)

    query += " ORDER BY p.nombre"

    cursor.execute(query, params)
    people = cursor.fetchall()
    conn.close()
    return people

def add_role(nombre):
    """Añade un nuevo rol a la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (nombre,))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Error: El rol '{nombre}' ya existe.")
        return False
    finally:
        conn.close()
    return True

def rename_role(rol_id, nuevo_nombre):
    """Renombra un rol existente."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE roles SET nombre = ? WHERE id = ?", (nuevo_nombre, rol_id))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Error: Ya existe un rol con el nombre '{nuevo_nombre}'.")
        return False
    finally:
        conn.close()
    return True

def delete_role(rol_id):
    """Elimina un rol de la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # La eliminación en cascada en la tabla personas_roles se encargará de las asociaciones
        cursor.execute("DELETE FROM roles WHERE id = ?", (rol_id,))
        conn.commit()
    finally:
        conn.close()

def add_roles_to_person(person_id, role_ids):
    """Añade una lista de roles a una persona, evitando duplicados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    asignaciones = [(person_id, rol_id) for rol_id in role_ids]
    # "OR IGNORE" es una sintaxis de SQLite para evitar errores de clave primaria duplicada
    cursor.executemany("INSERT OR IGNORE INTO personas_roles (persona_id, rol_id) VALUES (?, ?)", asignaciones)
    conn.commit()
    conn.close()

def remove_roles_from_person(person_id, role_ids):
    """Quita una lista de roles de una persona."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Para DELETE, necesitamos una tupla de tuplas para executemany
    asignaciones = [(person_id, rol_id) for rol_id in role_ids]
    cursor.executemany("DELETE FROM personas_roles WHERE persona_id = ? AND rol_id = ?", asignaciones)
    conn.commit()
    conn.close()

def update_person_gender(person_id, genero):
    """Actualiza solo el género de una persona."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personas SET genero = ? WHERE id = ?", (genero, person_id))
    conn.commit()
    conn.close()

def add_special_week(date_iso, reason):
    """Añade o actualiza una semana especial."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # INSERT OR REPLACE es una sintaxis de SQLite para hacer un 'upsert'
        cursor.execute("INSERT OR REPLACE INTO special_weeks (date, reason) VALUES (?, ?)", (date_iso, reason))
        conn.commit()
    finally:
        conn.close()

def remove_special_week(date_iso):
    """Elimina una semana especial."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM special_weeks WHERE date = ?", (date_iso,))
        conn.commit()
    finally:
        conn.close()

def get_special_week_reason(date_iso):
    """Obtiene el motivo de una semana especial. Devuelve None si no es especial."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT reason FROM special_weeks WHERE date = ?", (date_iso,))
    row = cursor.fetchone()
    conn.close()
    return row['reason'] if row else None

def get_special_weeks_for_month(year, month):
    """Obtiene todas las semanas especiales para un mes y año dados."""
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, reason FROM special_weeks WHERE date BETWEEN ? AND ?", (start_date, end_date))
    rows = cursor.fetchall()
    conn.close()
    return {row['date']: row['reason'] for row in rows}

def save_schedule_to_history(schedule):
    """
    Guarda un horario generado en la tabla de historial.
    El schedule es un dict: {'fecha': {'slot': 'nombre', ...}}
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for date_str, assignments in schedule.items():
            # Primero, borramos cualquier asignación existente para esa fecha para evitar duplicados
            cursor.execute("DELETE FROM asignaciones_historial WHERE fecha_reunion = ?", (date_str,))

            for slot, person_name in assignments.items():
                if person_name in ["---", "NADIE DISPONIBLE", "NO ENCONTRADO", None]:
                    continue

                # Obtener el ID de la persona
                cursor.execute("SELECT id FROM personas WHERE nombre = ?", (person_name,))
                person_row = cursor.fetchone()
                if person_row:
                    persona_id = person_row['id']
                    # Insertar el nuevo registro de historial
                    cursor.execute("""
                        INSERT INTO asignaciones_historial (persona_id, descripcion_asignacion, fecha_reunion)
                        VALUES (?, ?, ?)
                    """, (persona_id, slot, date_str))

        conn.commit()
        print(f"Historial de asignaciones para {len(schedule)} reuniones guardado.")
    except sqlite3.Error as e:
        print(f"Error al guardar el historial: {e}")
        conn.rollback()
    finally:
        conn.close()
