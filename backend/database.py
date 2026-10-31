import sqlite3
import os
import json
from datetime import datetime

def get_db_connection():
    db_file = os.environ.get("DATABASE_FILE", os.path.join(os.path.dirname(__file__), "voice_first.db"))
    conn = sqlite3.connect(db_file, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
    )
    """)

    # Notes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        note_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        session_id TEXT,
        subject TEXT NOT NULL,
        text TEXT NOT NULL,
        tag TEXT NOT NULL CHECK(tag IN ('Definition', 'Example', 'Important', 'General')),
        timestamp TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)

    # Correction history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS correction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id TEXT NOT NULL,
        original_text TEXT NOT NULL,
        corrected_text TEXT NOT NULL,
        correction_timestamp TEXT NOT NULL,
        change_reason TEXT,
        FOREIGN KEY (note_id) REFERENCES notes(note_id)
    )
    """)

    # Bookmarks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookmarks (
        id TEXT PRIMARY KEY,
        note_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        label TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (note_id) REFERENCES notes(note_id)
    )
    """)

    # Flashcards table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcards (
        id TEXT PRIMARY KEY,
        source_note_id TEXT,
        user_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        tag TEXT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        difficulty TEXT DEFAULT 'Medium' CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
        review_count INTEGER DEFAULT 0,
        correct_count INTEGER DEFAULT 0,
        last_reviewed_at TEXT,
        FOREIGN KEY (source_note_id) REFERENCES notes(note_id)
    )
    """)

    # Quiz history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_history (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        session_id TEXT,
        subject TEXT,
        question TEXT NOT NULL,
        user_spoken_answer TEXT,
        evaluation_result TEXT CHECK(evaluation_result IN ('Correct', 'Partially correct', 'Incorrect')),
        feedback TEXT,
        score REAL DEFAULT 0.0,
        timestamp TEXT NOT NULL,
        weakness_flag INTEGER DEFAULT 0
    )
    """)

    # Weak topics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weak_topics (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        topic TEXT NOT NULL,
        subject TEXT,
        error_count INTEGER DEFAULT 1,
        last_error_at TEXT NOT NULL,
        is_resolved INTEGER DEFAULT 0
    )
    """)

    # User settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id TEXT PRIMARY KEY,
        speech_rate REAL DEFAULT 1.0,
        speech_pitch REAL DEFAULT 1.0,
        speech_volume REAL DEFAULT 1.0,
        spoken_confirmation INTEGER DEFAULT 1,
        gemini_enabled INTEGER DEFAULT 1,
        updated_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

    # Seed sample notes if database has few notes
    seed_sample_notes_if_empty()

def seed_sample_notes_if_empty():
    conn = get_db_connection()
    cursor = conn.cursor()
    import uuid
    now_dt = datetime.now()
    now_iso = now_dt.isoformat()
    time_str = now_dt.strftime("%I:%M %p")
    default_user = "student_user_1"

    sample_notes = [
        # Biology
        ("Biology", "Mitosis is the process of cell division resulting in two genetically identical diploid daughter cells.", "Definition"),
        ("Biology", "For example, human skin cells and stem cells divide continuously through mitosis to replace damaged tissue.", "Example"),
        ("Biology", "Remember that the mitochondria is the powerhouse of the cell, generating adenosine triphosphate through oxidative phosphorylation.", "Important"),
        ("Biology", "Photosynthesis is the biochemical process by which green plant cells convert sunlight, water, and carbon dioxide into glucose and oxygen.", "Definition"),
        ("Biology", "General overview: Biology is the natural science that studies life and living organisms, including their physical structure and cellular processes.", "General"),
        ("Biology", "Important exam point: Cellular respiration occurs in mitochondria where glucose oxidation produces 36 to 38 ATP molecules per glucose molecule.", "Important"),

        # Computer Science
        ("Computer Science", "General overview: Computer science encompasses the theoretical foundations of computation, algorithms, data structures, and software engineering systems.", "General"),
        ("Computer Science", "General overview: Operating systems manage computer hardware, process scheduling, virtual memory management, and file system storage.", "General"),
        ("Computer Science", "Important exam point: Dijkstra's algorithm finds single-source shortest paths on graphs with non-negative edge weights in O of E plus V log V time.", "Important"),
        ("Computer Science", "Important exam point: A hash map provides average O of 1 time complexity for insertions, deletions, and key lookups.", "Important"),
        ("Computer Science", "Important exam point: The CAP theorem proves distributed data stores can simultaneously guarantee at most two of: Consistency, Availability, and Partition tolerance.", "Important"),
        ("Computer Science", "A binary search tree is a hierarchical data structure where every node has at most two children and left keys are less than root keys.", "Definition"),
        ("Computer Science", "For example, quicksort is a divide-and-conquer sorting algorithm that selects a pivot element and partitions the array.", "Example"),

        # Geography
        ("Geography", "General overview: Geography bridges natural physical sciences with human social systems by studying Earth's landscapes, environments, and spatial patterns.", "General"),
        ("Geography", "General overview: Earth's atmosphere consists of five primary layers: the troposphere where weather happens, stratosphere with the ozone layer, mesosphere, thermosphere, and exosphere.", "General"),
        ("Geography", "General overview: Global climate zones range from equatorial tropical rain forests to arid desert biomes and high-latitude arctic tundra.", "General"),
        ("Geography", "Important exam point: Plate tectonics explains continental drift, seismic fault lines, and volcanic mountain building at lithospheric plate boundaries.", "Important"),
        ("Geography", "Important exam point: The Prime Meridian at Greenwich defines zero degrees longitude, while the Equator defines zero degrees latitude for global timekeeping and navigation.", "Important"),
        ("Geography", "Important exam point: The Pacific Ring of Fire contains over 75 percent of Earth's active volcanoes and generates 90 percent of all earthquakes.", "Important"),
        ("Geography", "Plate tectonics is the scientific theory explaining how Earth's subterranean lithospheric plates move, interact, and create major landforms.", "Definition"),
        ("Geography", "For example, the collision of the Indian Plate with the Eurasian Plate formed the Himalayan mountain range and continues to cause seismic activity.", "Example"),

        # Chemistry
        ("Chemistry", "Boyle's law states that the pressure of a given mass of gas is inversely proportional to its volume at constant temperature.", "Definition"),
        ("Chemistry", "For example, squeezing a sealed syringe reduces gas volume and sharply increases pressure inside.", "Example"),
        ("Chemistry", "Important exam point: A covalent bond is formed by the sharing of electron pairs between nonmetal atoms.", "Important"),
        ("Chemistry", "General overview: Chemistry explores the composition, properties, and reactivity of matter at atomic and molecular scales.", "General"),

        # Physics
        ("Physics", "Newton's second law of motion states that acceleration is directly proportional to net force and inversely proportional to mass, F equals m a.", "Important"),
        ("Physics", "For example, pushing an empty cart produces much greater acceleration than a heavy cart with identical force.", "Example"),
        ("Physics", "Kinetic energy is the energy possessed by an object due to its motion, calculated as one-half mass times velocity squared.", "Definition"),
        ("Physics", "General overview: Physics is the fundamental science studying matter, energy, spacetime, and the universal forces governing physical reality.", "General"),

        # Mathematics
        ("Mathematics", "The derivative of a function measures the instantaneous rate of change of the function with respect to its variable.", "Definition"),
        ("Mathematics", "For example, by the power rule, the derivative of x cubed is three x squared.", "Example"),
        ("Mathematics", "Important exam point: The fundamental theorem of calculus establishes that differentiation and integration are inverse operations.", "Important"),
        ("Mathematics", "General overview: Mathematics provides quantitative language and formal structures for modeling continuous and discrete phenomena.", "General")
    ]

    for subj, text, tag in sample_notes:
        cursor.execute("SELECT 1 FROM notes WHERE text = ? AND is_deleted = 0", (text,))
        if not cursor.fetchone():
            note_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notes (note_id, user_id, session_id, subject, text, tag, timestamp, confidence, created_at, updated_at, is_deleted)
                VALUES (?, ?, NULL, ?, ?, ?, ?, 1.0, ?, ?, 0)
            """, (note_id, default_user, subj, text, tag, time_str, now_iso, now_iso))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
