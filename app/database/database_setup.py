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
        nombre TEXT NOT NULL UNIQUE,
        genero TEXT NOT NULL DEFAULT 'No especificado' CHECK(genero IN ('Hombre', 'Mujer', 'No especificado'))
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

    sql_create_special_weeks_table = """
    CREATE TABLE IF NOT EXISTS special_weeks (
        date DATE PRIMARY KEY,
        reason TEXT NOT NULL
    );
    """

    sql_create_meeting_template_table = """
    CREATE TABLE IF NOT EXISTS meeting_template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_type INTEGER NOT NULL,
        row_index INTEGER NOT NULL,
        col_index INTEGER NOT NULL,
        assignment_text TEXT NOT NULL,
        is_editable INTEGER NOT NULL DEFAULT 0,
        UNIQUE(week_type, row_index, col_index)
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
        create_table(conn, sql_create_special_weeks_table)
        create_table(conn, sql_create_meeting_template_table)

        cursor = conn.cursor()

        # --- Handle migration for existing databases: add 'genero' column if it doesn't exist ---
        cursor.execute("PRAGMA table_info(personas)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'genero' not in columns:
            print("Añadiendo columna 'genero' a la tabla 'personas'.")
            # Note: The CHECK constraint might not be enforceable on ALTER TABLE in older SQLite versions,
            # but it's good practice to include it. The application logic will be the primary guard.
            cursor.execute("ALTER TABLE personas ADD COLUMN genero TEXT NOT NULL DEFAULT 'No especificado'")
            # A separate CHECK constraint is not easily added via ALTER TABLE.
            # The CREATE TABLE statement will handle it for new DBs.
            conn.commit()

        # --- Data Migration for meeting_template ---
        cursor.execute("SELECT COUNT(*) FROM meeting_template")
        if cursor.fetchone()[0] == 0:
            print("Migrando plantilla de reunión a la base de datos...")
            # La plantilla ahora se define aquí temporalmente para la migración
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
            rows_to_insert = []
            for week_type, week_template in enumerate(USER_TEMPLATE_STRUCTURE):
                for row_idx, row_data in enumerate(week_template):
                    for col_idx, cell_text in enumerate(row_data):
                        # Marcar temas específicos como editables
                        is_editable = 0
                        # Tema de Tesoros: semana_X, fila_3, col_0
                        # Tema de Vida Cristiana: semana_X, fila_10, col_1
                        if (row_idx == 3 and col_idx == 0) or (row_idx == 10 and col_idx == 1):
                            is_editable = 1

                        rows_to_insert.append((week_type, row_idx, col_idx, cell_text, is_editable))

            cursor.executemany(
                "INSERT INTO meeting_template (week_type, row_index, col_index, assignment_text, is_editable) VALUES (?, ?, ?, ?, ?)",
                rows_to_insert
            )
            conn.commit()
            print("Migración de plantilla completada.")

        # Opcional: Añadir roles por defecto si la tabla está vacía
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
