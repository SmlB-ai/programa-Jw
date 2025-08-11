import sqlite3
import os

DB_FILE = "asignaciones.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_FILE)

def create_connection():
    """Crea una conexión a la base de datos SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        print(f"Conexión exitosa a la base de datos en {DB_PATH}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    """Crea una tabla a partir de la declaración SQL proporcionada."""
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def setup_database():
    """Crea las tablas necesarias en la base de datos."""

    sql_create_personas_table = """
    CREATE TABLE IF NOT EXISTS personas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    );
    """

    sql_create_roles_table = """
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE
    );
    """

    sql_create_personas_roles_table = """
    CREATE TABLE IF NOT EXISTS personas_roles (
        persona_id INTEGER NOT NULL,
        rol_id INTEGER NOT NULL,
        PRIMARY KEY (persona_id, rol_id),
        FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE,
        FOREIGN KEY (rol_id) REFERENCES roles (id) ON DELETE CASCADE
    );
    """

    sql_create_asignaciones_historial_table = """
    CREATE TABLE IF NOT EXISTS asignaciones_historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        persona_id INTEGER NOT NULL,
        descripcion_asignacion TEXT NOT NULL,
        fecha_reunion DATE NOT NULL,
        FOREIGN KEY (persona_id) REFERENCES personas (id) ON DELETE CASCADE
    );
    """

    # Crear conexión a la base de datos
    conn = create_connection()

    # Crear tablas
    if conn is not None:
        create_table(conn, sql_create_personas_table)
        create_table(conn, sql_create_roles_table)
        create_table(conn, sql_create_personas_roles_table)
        create_table(conn, sql_create_asignaciones_historial_table)

        # Opcional: Añadir roles por defecto si la tabla está vacía
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM roles")
        if cursor.fetchone()[0] == 0:
            default_roles = [
                ('Anciano',),
                ('Siervo Ministerial',),
                ('Lector',),
                ('Acomodador',),
                ('Presidente',),
                ('Oración',),
                ('Discurso',),
                ('Estudio Bíblico Conductor',),
                ('Estudio Bíblico Lector',)
            ]
            cursor.executemany("INSERT INTO roles (nombre) VALUES (?)", default_roles)
            conn.commit()
            print("Roles por defecto insertados.")

        conn.close()
        print("Base de datos configurada correctamente.")
    else:
        print("Error: No se pudo crear la conexión a la base de datos.")

if __name__ == '__main__':
    setup_database()
