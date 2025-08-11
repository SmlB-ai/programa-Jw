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

def get_all_people_with_roles():
    """Obtiene todas las personas y sus roles asociados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.id, p.nombre, GROUP_CONCAT(r.nombre, ', ') as roles
    FROM personas p
    LEFT JOIN personas_roles pr ON p.id = pr.persona_id
    LEFT JOIN roles r ON pr.rol_id = r.id
    GROUP BY p.id
    ORDER BY p.nombre
    """
    cursor.execute(query)
    people = cursor.fetchall()
    conn.close()
    return people

def add_person_with_roles(nombre, rol_ids):
    """Añade una nueva persona y le asigna roles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO personas (nombre) VALUES (?)", (nombre,))
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

def update_person_with_roles(persona_id, nombre, rol_ids):
    """Actualiza el nombre de una persona y sus roles."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Actualizar nombre
        cursor.execute("UPDATE personas SET nombre = ? WHERE id = ?", (nombre, persona_id))

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
    """Obtiene los detalles de una persona, incluyendo sus IDs de rol."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener nombre
    cursor.execute("SELECT nombre FROM personas WHERE id = ?", (persona_id,))
    persona = cursor.fetchone()
    if not persona:
        conn.close()
        return None, None

    # Obtener roles
    cursor.execute("SELECT rol_id FROM personas_roles WHERE persona_id = ?", (persona_id,))
    rol_ids = [row['rol_id'] for row in cursor.fetchall()]

    conn.close()
    return persona['nombre'], rol_ids

def get_people_for_role(role_name):
    """Obtiene todas las personas que tienen un rol específico."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT p.id, p.nombre
    FROM personas p
    JOIN personas_roles pr ON p.id = pr.persona_id
    JOIN roles r ON pr.rol_id = r.id
    WHERE r.nombre = ?
    ORDER BY p.nombre
    """
    cursor.execute(query, (role_name,))
    people = cursor.fetchall()
    conn.close()
    return people

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
