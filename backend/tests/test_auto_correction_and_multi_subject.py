import os
import pytest
import tempfile

temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_FILE"] = temp_db.name

import database
from app import app
from services.auto_correction_service import AutoSpeechCorrectionService
from services.academic_knowledge_service import AcademicKnowledgeService
from services.note_service import NoteService
from services.flashcard_service import FlashcardService
from services.quiz_service import QuizService

@pytest.fixture(autouse=True)
def setup_and_teardown():
    key_file = os.path.join(os.path.dirname(__file__), "..", "gemini_key.txt")
    if os.path.exists(key_file):
        try:
            os.remove(key_file)
        except Exception:
            pass
    from app import gemini_service
    gemini_service.api_key = ""
    gemini_service.client = None

    database.init_db()
    yield
    if os.path.exists(key_file):
        try:
            os.remove(key_file)
        except Exception:
            pass
    gemini_service.api_key = ""
    gemini_service.client = None

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM correction_history")
    cursor.execute("DELETE FROM bookmarks")
    cursor.execute("DELETE FROM flashcards")
    cursor.execute("DELETE FROM quiz_history")
    cursor.execute("DELETE FROM weak_topics")
    cursor.execute("DELETE FROM notes")
    cursor.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_auto_speech_correction_unit():
    # Test command correction
    c1, _ = AutoSpeechCorrectionService.correct_transcript("quize me on camistry")
    assert "quiz me on Chemistry" in c1

    # Test phonetic biology correction
    c2, _ = AutoSpeechCorrectionService.correct_transcript("my toes is is sell division")
    assert "mitosis" in c2
    assert "cell division" in c2

    # Test chemistry term correction
    c3, _ = AutoSpeechCorrectionService.correct_transcript("boyle slaw states pressure is inversely proportional")
    assert "Boyle's law" in c3

    # Test computer science correction
    c4, _ = AutoSpeechCorrectionService.correct_transcript("pythun algo rithm with big o notation")
    assert "Python" in c4
    assert "algorithm" in c4
    assert "Big O notation" in c4

    # Test physics correction
    c5, _ = AutoSpeechCorrectionService.correct_transcript("new ton second law of motion")
    assert "Newton's" in c5

def test_subject_domain_auto_detection():
    assert AutoSpeechCorrectionService.detect_subject("Boyle's law states pressure and volume change") == "Chemistry"
    assert AutoSpeechCorrectionService.detect_subject("Newton's second law is force equals mass times acceleration") == "Physics"
    assert AutoSpeechCorrectionService.detect_subject("Binary search runs in O of log N time complexity") == "Computer Science"
    assert AutoSpeechCorrectionService.detect_subject("The derivative of x squared is 2x") == "Mathematics"
    assert AutoSpeechCorrectionService.detect_subject("The Treaty of Versailles concluded World War I") == "History"
    assert AutoSpeechCorrectionService.detect_subject("Mitosis produces two diploid daughter cells") == "Biology"

def test_multi_subject_quiz_and_flashcards_generation(client):
    user_id = "multi_student"

    # 1. Spoken input with speech typo "camistry"
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "quize me on camistry"})
    d1 = r1.get_json()
    assert d1["intent"] == "QUIZ_ME"
    assert "Chemistry" in d1["spoken_response"]
    assert d1["data"]["type"] == "quiz"
    assert len(d1["data"]["questions"]) >= 5

    # Verify that Chemistry notes were permanently saved into SQLite
    chem_notes = NoteService.get_notes_by_filter(user_id, subject="Chemistry")
    assert len(chem_notes) >= 5

    # 2. Spoken input for Physics flashcards
    r2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "Make flashcards on Physics"})
    d2 = r2.get_json()
    assert d2["intent"] == "FLASHCARDS"
    assert "Physics" in d2["spoken_response"]
    assert d2["data"]["type"] == "flashcards"
    assert len(d2["data"]["cards"]) >= 8

    # Verify Physics notes stored in SQLite
    phys_notes = NoteService.get_notes_by_filter(user_id, subject="Physics")
    assert len(phys_notes) >= 5

    # 3. Spoken input for Computer Science Quiz
    r3 = client.post("/api/voice/process", json={"user_id": user_id, "text": "Quiz me on Computer Science"})
    d3 = r3.get_json()
    assert d3["intent"] == "QUIZ_ME"
    assert "Computer Science" in d3["spoken_response"]
    assert len(d3["data"]["questions"]) >= 5

    # 4. Spoken input for Mathematics Flashcards
    r4 = client.post("/api/voice/process", json={"user_id": user_id, "text": "Give me flashcards for Mathematics"})
    d4 = r4.get_json()
    assert d4["intent"] == "FLASHCARDS"
    assert "Mathematics" in d4["spoken_response"]
    assert len(d4["data"]["cards"]) >= 8

def test_gemini_key_settings_endpoint(client):
    # GET settings
    r_get = client.get("/api/settings/gemini_key")
    assert r_get.status_code == 200
    d_get = r_get.get_json()
    assert "gemini_available" in d_get
    assert "has_key" in d_get

    # POST dummy key (fails gracefully without crashing)
    r_post = client.post("/api/settings/gemini_key", json={"api_key": "dummy_test_key_12345"})
    assert r_post.status_code in [200, 400]

def test_flashcard_flip_and_next_controls(client):
    user_id = "student_flip_test"
    # Seed notes
    NoteService.create_note(user_id, "Photosynthesis is the conversion of light into chemical energy.", subject="Biology")
    NoteService.create_note(user_id, "Mitosis produces two genetically identical diploid cells.", subject="Biology")

    # 1. Start flashcards
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "Start flashcards on Biology"})
    d1 = r1.get_json()
    assert d1["intent"] == "FLASHCARDS"
    ctx = d1["context"]
    assert ctx["current_mode"] == "flashcard_active"
    assert len(ctx["flashcards"]) >= 2
    assert ctx["current_card_index"] == 0

    # 2. Say "flip" -> reveals answer (is_flipped = True)
    r2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "flip", "context": ctx})
    d2 = r2.get_json()
    assert d2["intent"] == "FLASHCARD_FLIP"
    assert d2["data"]["is_flipped"] is True
    assert "answer is" in d2["spoken_response"].lower()
    ctx2 = d2["context"]
    assert ctx2["is_card_flipped"] is True

    # 3. Say "flip" again -> flips back to question (is_flipped = False)
    r3 = client.post("/api/voice/process", json={"user_id": user_id, "text": "flip", "context": ctx2})
    d3 = r3.get_json()
    assert d3["intent"] == "FLASHCARD_FLIP"
    assert d3["data"]["is_flipped"] is False
    assert "flipped" in d3["spoken_response"].lower()
    ctx3 = d3["context"]
    assert ctx3["is_card_flipped"] is False

    # 4. Say "next" -> advances to card 2 (is_flipped = False)
    r4 = client.post("/api/voice/process", json={"user_id": user_id, "text": "next", "context": ctx3})
    d4 = r4.get_json()
    assert d4["intent"] in ["AUDIO_NEXT", "FLASHCARD_SKIP"]
    assert d4["action"] == "FLASHCARD_INDEX_UPDATED"
    assert d4["data"]["current_index"] == 1
    assert d4["data"]["is_flipped"] is False
    assert "Card 2" in d4["spoken_response"]

    # 5. Say "previous" -> moves back to card 1
    ctx4 = d4["context"]
    r5 = client.post("/api/voice/process", json={"user_id": user_id, "text": "previous", "context": ctx4})
    d5 = r5.get_json()
    assert d5["intent"] == "AUDIO_PREVIOUS"
    assert d5["action"] == "FLASHCARD_INDEX_UPDATED"
    assert d5["data"]["current_index"] == 0
    assert "Card 1" in d5["spoken_response"]

def test_recent_notes_by_subject(client):
    user_id = "student_recents_test"
    NoteService.create_note(user_id, "Boyle's law states that pressure and volume are inversely related.", subject="Physics")
    NoteService.create_note(user_id, "Covalent bonds involve electron sharing.", subject="Chemistry")

    # 1. "read recent notes"
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "read recent notes"})
    d1 = r1.get_json()
    assert d1["intent"] == "READ_RECENT_NOTES"
    assert d1["action"] == "NAVIGATE_AUDIO_REVIEW"
    assert len(d1["data"]["notes"]) >= 2
    assert "recent notes" in d1["spoken_response"].lower()

    # 2. "recent notes for Chemistry"
    r2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "recent notes for Chemistry"})
    d2 = r2.get_json()
    assert d2["intent"] == "READ_RECENT_NOTES"
    assert d2["action"] == "NAVIGATE_AUDIO_REVIEW"
    assert "Chemistry" in d2["spoken_response"]

def test_delete_note_and_recents_navigation(client):
    user_id = "student_delete_test"
    # Create a wrong note
    note = NoteService.create_note(user_id, "Wrong note captured by mistake in biology lecture.", subject="Biology")
    note_id = note["note_id"]

    # 1. Voice navigation to recents
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "open recents"})
    d1 = r1.get_json()
    assert d1["intent"] == "OPEN_RECENTS"
    assert d1["action"] == "NAVIGATE_RECENTS"
    assert "Opening recent recordings" in d1["spoken_response"]

    # 2. Voice command to delete last note
    r2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "delete last note"})
    d2 = r2.get_json()
    assert d2["intent"] == "DELETE_NOTE"
    assert d2["action"] == "NOTE_DELETED"
    assert "Deleted note" in d2["spoken_response"]

    # Verify note is deleted in DB
    remaining_notes = NoteService.get_notes_by_filter(user_id)
    assert not any(n["note_id"] == note_id for n in remaining_notes)

    # 3. Test REST DELETE /api/notes/<note_id>
    note2 = NoteService.create_note(user_id, "Another wrong note to delete via REST.", subject="Chemistry")
    r3 = client.delete(f"/api/notes/{note2['note_id']}?user_id={user_id}")
    assert r3.status_code == 200
    assert r3.get_json()["success"] is True

def test_geography_and_cs_general_and_important_notes(client):
    # 1. Phonetic speech auto-correction for Geography terminology
    corrected, fixed = AutoSpeechCorrectionService.correct_transcript("Take a note for geogrophy on plate tektonics and the lithosfear")
    assert "Geography" in corrected
    assert "plate tectonics" in corrected
    assert "lithosphere" in corrected

    # 2. Domain auto-detection for Geography
    subj = AutoSpeechCorrectionService.detect_subject("The troposphere and stratosphere regulate global climate zones")
    assert subj == "Geography"

    # 3. Verify sample notes in DB have General and Important tags for Geography and Computer Science
    import database
    database.seed_sample_notes_if_empty()

    geo_notes = NoteService.get_notes_by_filter("student_user_1", subject="Geography")
    assert len(geo_notes) >= 4
    geo_tags = {n["tag"] for n in geo_notes}
    assert "General" in geo_tags
    assert "Important" in geo_tags
    assert "Definition" in geo_tags
    assert "Example" in geo_tags

    cs_notes = NoteService.get_notes_by_filter("student_user_1", subject="Computer Science")
    assert len(cs_notes) >= 4
    cs_tags = {n["tag"] for n in cs_notes}
    assert "General" in cs_tags
    assert "Important" in cs_tags

    # 4. Spoken command for Geography Flashcards
    r_fc = client.post("/api/voice/process", json={"user_id": "student_user_1", "text": "Give me flashcards for Geography"})
    d_fc = r_fc.get_json()
    assert d_fc["intent"] == "FLASHCARDS"
    assert "Geography" in d_fc["spoken_response"]
    assert len(d_fc["data"]["cards"]) >= 8

    # 5. Spoken command for Geography Quiz
    r_qz = client.post("/api/voice/process", json={"user_id": "student_user_1", "text": "Quiz me on Geography"})
    d_qz = r_qz.get_json()
    assert d_qz["intent"] in ["QUIZ_ME", "START_QUIZ"]
    assert "Geography" in d_qz["spoken_response"]
    assert len(d_qz["data"]["questions"]) >= 5

    # 6. Spoken command for Recent Notes for Computer Science and Geography
    r_rec_cs = client.post("/api/voice/process", json={"user_id": "student_user_1", "text": "recent notes for Computer Science"})
    assert r_rec_cs.get_json()["intent"] == "READ_RECENT_NOTES"

    r_rec_geo = client.post("/api/voice/process", json={"user_id": "student_user_1", "text": "recent notes for Geography"})
    assert r_rec_geo.get_json()["intent"] == "READ_RECENT_NOTES"

def test_comprehensive_search_notes_functionality(client):
    user_id = "student_search_test"
    NoteService.create_note(user_id, "Mitosis is the process of cell division resulting in identical cells.", subject="Biology", explicit_tag="Definition")
    NoteService.create_note(user_id, "Photosynthesis converts light and carbon dioxide into glucose.", subject="Biology", explicit_tag="Important")
    NoteService.create_note(user_id, "Plate tectonics explains continental drift and mountain building.", subject="Geography", explicit_tag="Important")

    # 1. Open Search screen navigation
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "search notes"})
    d1 = r1.get_json()
    assert d1["intent"] == "OPEN_SEARCH"
    assert d1["action"] == "NAVIGATE_RETRIEVAL"
    assert "search screen" in d1["spoken_response"].lower()
    ctx1 = d1["context"]
    assert ctx1["current_mode"] == "retrieval"

    # 2. Open Search via "open search"
    r2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "open search"})
    assert r2.get_json()["intent"] == "OPEN_SEARCH"

    # 3. Direct Search command: "search mitosis"
    r3 = client.post("/api/voice/process", json={"user_id": user_id, "text": "search mitosis"})
    d3 = r3.get_json()
    assert d3["intent"] == "SEARCH_NOTES"
    assert d3["action"] == "NAVIGATE_RETRIEVAL"
    assert len(d3["data"]["results"]) >= 1
    assert "Found 1 note about mitosis" in d3["spoken_response"]
    ctx3 = d3["context"]
    assert ctx3["current_mode"] == "retrieval"

    # 4. Search command: "find photosynthesis"
    r4 = client.post("/api/voice/process", json={"user_id": user_id, "text": "find photosynthesis"})
    d4 = r4.get_json()
    assert d4["intent"] == "SEARCH_NOTES"
    assert len(d4["data"]["results"]) >= 1

    # 5. Search command with phrasing: "search notes for plate tectonics"
    r5 = client.post("/api/voice/process", json={"user_id": user_id, "text": "search notes for plate tectonics"})
    d5 = r5.get_json()
    assert d5["intent"] == "SEARCH_NOTES"
    assert len(d5["data"]["results"]) >= 1
    assert "plate tectonics" in d5["spoken_response"].lower()

    # 6. Contextual retrieval mode: student is in retrieval mode and simply speaks topic keyword
    r6 = client.post("/api/voice/process", json={"user_id": user_id, "text": "mitosis", "context": {"current_mode": "retrieval"}})
    d6 = r6.get_json()
    assert d6["intent"] == "SEARCH_NOTES"
    assert len(d6["data"]["results"]) >= 1

    # 7. Navigation in search results: Next / Repeat / Stop
    ctx_search = d3["context"]
    # Add a second mitosis note to test Next
    NoteService.create_note(user_id, "Skin cells divide through mitosis continuously.", subject="Biology")
    r_search2 = client.post("/api/voice/process", json={"user_id": user_id, "text": "search mitosis"})
    ctx_search2 = r_search2.get_json()["context"]
    assert len(r_search2.get_json()["data"]["results"]) == 2

    # Say "next"
    r_next = client.post("/api/voice/process", json={"user_id": user_id, "text": "next", "context": ctx_search2})
    d_next = r_next.get_json()
    assert d_next["intent"] == "AUDIO_NEXT"
    assert d_next["action"] == "AUDIO_INDEX_UPDATED"
    assert d_next["data"]["current_index"] == 1

    # Say "repeat"
    r_rep = client.post("/api/voice/process", json={"user_id": user_id, "text": "repeat", "context": d_next["context"]})
    assert r_rep.get_json()["intent"] == "AUDIO_REPEAT"

    # 8. REST endpoint /api/search
    r_rest = client.get(f"/api/search?user_id={user_id}&q=photosynthesis")
    assert r_rest.status_code == 200
    d_rest = r_rest.get_json()
    assert len(d_rest) >= 1
    assert "glucose" in d_rest[0]["text"]


def test_cross_domain_subject_isolation_and_geography_notes(client):
    user_id = "student_cross_domain_test"

    # 1. Start a Biology lecture session
    r1 = client.post("/api/voice/process", json={"user_id": user_id, "text": "start Biology lecture"})
    d1 = r1.get_json()
    assert d1["intent"] == "START_LECTURE"
    ctx1 = d1["context"]
    assert ctx1["current_subject"] == "Biology"
    assert ctx1["current_session_id"] is not None

    # 2. Dictate a Geography note while Biology lecture was active in context
    # Should automatically detect domain mismatch and store under Geography
    r2 = client.post("/api/voice/process", json={
        "user_id": user_id,
        "text": "Geography is the study of the four foundational branches including continental drift and endogenic processes",
        "context": ctx1
    })
    d2 = r2.get_json()
    assert d2["intent"] == "CREATE_NOTE"
    note = d2["data"]["note"]
    assert note["subject"] == "Geography"

    # 3. Voice command "start Geography notes" should switch session to Geography, NOT create a note
    r3 = client.post("/api/voice/process", json={"user_id": user_id, "text": "start Geography notes", "context": ctx1})
    d3 = r3.get_json()
    assert d3["intent"] == "START_LECTURE"
    assert d3["data"]["session"]["subject"] == "Geography"
    ctx3 = d3["context"]
    assert ctx3["current_subject"] == "Geography"

    # 4. Voice command "retrieve Geography note" should trigger SEARCH_NOTES, NOT CREATE_NOTE
    r4 = client.post("/api/voice/process", json={"user_id": user_id, "text": "retrieve Geography note", "context": ctx3})
    d4 = r4.get_json()
    assert d4["intent"] == "SEARCH_NOTES"
    assert d4["action"] == "NAVIGATE_RETRIEVAL"
    assert len(d4["data"]["results"]) >= 1
    assert d4["data"]["results"][0]["subject"] == "Geography"

def test_analytics_service_and_voice_intent(client):
    user_id = "test_analytics_user"
    
    # 1. Create a few notes with different subjects and tags
    client.post("/api/voice/process", json={
        "user_id": user_id,
        "text": "Note important: Mitosis is cell division in eukaryotic cells.",
        "context": {}
    })
    client.post("/api/voice/process", json={
        "user_id": user_id,
        "text": "Note: Plate tectonics explains continental drift in geography.",
        "context": {}
    })
    client.post("/api/voice/process", json={
        "user_id": user_id,
        "text": "Note definition: Binary search is an efficient search algorithm in computer science.",
        "context": {}
    })

    # 2. Test GET /api/analytics endpoint
    res = client.get(f"/api/analytics?user_id={user_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_notes"] >= 3
    assert "subject_counts" in data
    assert "tag_counts" in data
    assert "concept_nodes" in data
    assert "spoken_summary" in data
    assert "Biology" in data["subject_counts"] or "Geography" in data["subject_counts"]

    # 3. Test voice command "open analytics"
    v_res = client.post("/api/voice/process", json={"user_id": user_id, "text": "open analytics", "context": {}})
    v_data = v_res.get_json()
    assert v_data["intent"] == "OPEN_ANALYTICS"
    assert v_data["action"] == "NAVIGATE_ANALYTICS"
    assert "analytics" in v_data["data"]
    assert "Study analytics summary" in v_data["spoken_response"]

    # 4. Test alternate voice commands "show graphs" and "study stats"
    g_res = client.post("/api/voice/process", json={"user_id": user_id, "text": "show visual graphs", "context": {}})
    assert g_res.get_json()["intent"] == "OPEN_ANALYTICS"

    s_res = client.post("/api/voice/process", json={"user_id": user_id, "text": "study stats", "context": {}})
    assert s_res.get_json()["intent"] == "OPEN_ANALYTICS"





