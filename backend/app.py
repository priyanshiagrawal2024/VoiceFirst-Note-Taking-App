import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from database import init_db
from services.intent_parser import IntentParser
from services.note_service import NoteService
from services.correction_service import CorrectionService
from services.search_service import SearchService
from services.bookmark_service import BookmarkService
from services.timeline_service import TimelineService
from services.flashcard_service import FlashcardService
from services.quiz_service import QuizService
from services.gemini_service import GeminiService
from services.auto_correction_service import AutoSpeechCorrectionService
from services.academic_knowledge_service import AcademicKnowledgeService

app = Flask(__name__)
CORS(app)

# Initialize Database and Services
init_db()
gemini_service = GeminiService()
intent_parser = IntentParser(gemini_service=gemini_service)

DEFAULT_USER_ID = "student_user_1"

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Voice-First Backend",
        "gemini_available": gemini_service.is_available()
    })

# =========================================================================
# Voice Intent Router - Central Voice Pipeline
# =========================================================================
@app.route("/api/voice/process", methods=["POST"])
def process_voice():
    """
    Main voice processing pipeline.
    Receives raw recognized speech + conversation context.
    Executes business logic, updates SQLite, and returns spoken response.
    """
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    user_id = data.get("user_id", DEFAULT_USER_ID)
    context = data.get("context", {})

    if not text:
        return jsonify({
            "intent": "EMPTY",
            "spoken_response": "I didn't hear anything. Please speak your command or note.",
            "action": "none",
            "context": context
        })

    # Step 0: Intelligent Speech Auto-Correction (Phonetic & Academic Terminology Repair)
    raw_text = text
    cleaned_text, corrections = AutoSpeechCorrectionService.correct_transcript(
        raw_text, gemini_service=gemini_service, context=context
    )
    if cleaned_text:
        text = cleaned_text

    # Step 1: Parse Intent (Regex first, Gemini fallback)
    parsed = intent_parser.parse(text, context=context)
    intent = parsed["intent"]
    entities = parsed["entities"]

    spoken_response = "I couldn't understand that. Please repeat, or say Help."
    action = "none"
    response_data = {}
    next_context = dict(context)

    # ---------------------------------------------------------------------
    # Core Phase Commands
    # ---------------------------------------------------------------------
    if intent == "START_LECTURE":
        subject = entities.get("subject", "General")
        session = NoteService.start_session(user_id, subject)
        spoken_response = f"Started {session['subject']} lecture. Voice-First is ready for your notes."
        action = "NAVIGATE_ACTIVE_LECTURE"
        response_data = {"session": session}
        next_context.update({
            "current_mode": "active_lecture",
            "current_session_id": session["session_id"],
            "current_subject": session["subject"]
        })

    elif intent == "END_LECTURE":
        session = NoteService.end_active_session(user_id)
        if session:
            spoken_response = f"{session['subject']} lecture ended. Total {session['note_count']} notes saved."
            action = "NAVIGATE_HOME"
            response_data = {"session": session}
        else:
            spoken_response = "No active lecture session to end."
            action = "none"
        next_context.update({
            "current_mode": "home",
            "current_session_id": None,
            "current_subject": None
        })

    elif intent == "CREATE_NOTE":
        content = entities.get("content", text)
        confidence = float(data.get("confidence", 1.0))
        active_sess_id = next_context.get("current_session_id")
        active_subj = next_context.get("current_subject")
        current_mode = next_context.get("current_mode", "home")
        
        note = NoteService.create_note(
            user_id=user_id,
            text=content,
            subject=active_subj,
            session_id=active_sess_id,
            confidence=confidence
        )
        action = "NOTE_CREATED"
        response_data = {"note": note}
        next_context["last_note_id"] = note["note_id"]
        next_context["last_note_text"] = note["text"]

        # In active lecture mode, do NOT read back captured notes aloud (silent continuous capture)
        # UNLESS the note was cross-domain redirected, then announce it clearly!
        if (current_mode == "active_lecture" or active_sess_id) and (not active_subj or note["subject"].lower() == active_subj.lower()):
            spoken_response = ""
        else:
            tag_announcement = f" Tagged as {note['tag']}." if note['tag'] != 'General' else ""
            spoken_response = f"Saved {note['subject']} note: {note['text']}.{tag_announcement}"

    elif intent == "TAG_NOTE":
        tag = entities.get("tag", "Important")
        last_note_id = next_context.get("last_note_id")
        if not last_note_id:
            last_note = NoteService.get_last_note(user_id)
            if last_note:
                last_note_id = last_note["note_id"]

        if last_note_id:
            updated = NoteService.update_tag(last_note_id, tag)
            spoken_response = f"Tagged as {updated['tag']}."
            action = "NOTE_UPDATED"
            response_data = {"note": updated}
        else:
            spoken_response = "You don't have any notes to tag yet."

    elif intent == "CORRECT_NOTE_REPLACE":
        target = entities.get("target", "")
        replacement = entities.get("replacement", "")
        last_note_id = next_context.get("last_note_id")
        
        success, speech, updated_note = CorrectionService.correct_word_replacement(
            user_id=user_id,
            target=target,
            replacement=replacement,
            note_id=last_note_id
        )
        spoken_response = speech
        if success and updated_note:
            action = "NOTE_CORRECTED"
            response_data = {"note": updated_note}
            next_context["last_note_text"] = updated_note["text"]

    elif intent == "CORRECT_NOTE_FULL":
        new_content = entities.get("new_content", "")
        last_note_id = next_context.get("last_note_id")
        
        success, speech, updated_note = CorrectionService.correct_full_text(
            user_id=user_id,
            new_text=new_content,
            note_id=last_note_id
        )
        spoken_response = speech
        if success and updated_note:
            action = "NOTE_CORRECTED"
            response_data = {"note": updated_note}
            next_context["last_note_text"] = updated_note["text"]

    elif intent == "CORRECT_LAST_NOTE_PROMPT":
        last_note = NoteService.get_last_note(user_id)
        if last_note:
            spoken_response = f"Your last note says: {last_note['text']}. Say 'Correct [word] to [word]' or dictate the replacement note."
        else:
            spoken_response = "You don't have any notes to correct yet."

    elif intent == "DELETE_NOTE":
        note_id_to_delete = entities.get("note_id") or next_context.get("last_note_id")
        target_note = None
        if note_id_to_delete:
            target_note = NoteService.get_last_note(user_id)
        if not target_note:
            target_note = NoteService.get_last_note(user_id)

        if target_note:
            NoteService.delete_note(target_note["note_id"], user_id)
            spoken_response = f"Deleted note: {target_note['text']}."
            action = "NOTE_DELETED"
            response_data = {"note_id": target_note["note_id"], "note": target_note}
            next_context["last_note_id"] = None
            next_context["last_note_text"] = None
        else:
            spoken_response = "You don't have any recent notes to delete."
            action = "none"

    elif intent == "OPEN_RECENTS":
        notes = NoteService.get_notes_by_filter(user_id)
        count = len(notes)
        spoken_response = f"Opening recent recordings. You have {count} recent notes. Tap any recording to listen, filter by subject, or delete unwanted notes."
        action = "NAVIGATE_RECENTS"
        response_data = {"notes": notes}
        next_context["current_mode"] = "recents"

    elif intent == "OPEN_ANALYTICS":
        analytics = NoteService.get_analytics(user_id)
        spoken_response = analytics["spoken_summary"]
        action = "NAVIGATE_ANALYTICS"
        response_data = {"analytics": analytics}
        next_context["current_mode"] = "analytics"

    elif intent == "OPEN_SEARCH":
        notes = NoteService.get_notes_by_filter(user_id)
        count = len(notes)
        spoken_response = f"Opening search screen. You have {count} notes. What topic or keyword would you like to search for?"
        action = "NAVIGATE_RETRIEVAL"
        response_data = {"results": notes, "query": "", "current_index": 0}
        next_context.update({
            "current_mode": "retrieval",
            "search_results": notes,
            "search_query": "",
            "current_index": 0
        })

    elif intent == "SEARCH_NOTES" or intent == "CONTEXTUAL_SEARCH":
        query = entities.get("query", "").strip()
        results = SearchService.search_notes(user_id, query)
        
        # If regex search returned 0 and Gemini available, try contextual fuzzy search
        if not results and gemini_service.is_available():
            all_notes = NoteService.get_notes_by_filter(user_id)
            fuzzy_results = gemini_service.contextual_fuzzy_search(query, all_notes)
            if fuzzy_results:
                results = fuzzy_results

        spoken_response = SearchService.format_search_speech(results, query, index=0)
        action = "NAVIGATE_RETRIEVAL"
        response_data = {"results": results, "query": query, "current_index": 0}
        next_context.update({
            "current_mode": "retrieval",
            "search_results": results,
            "search_query": query,
            "current_index": 0
        })

    elif intent in ["READ_TODAYS_NOTES", "READ_WEEKS_NOTES", "READ_SUBJECT_NOTES", "READ_RECENT_NOTES", "AUDIO_SKIM"]:
        subject = entities.get("subject")
        timeframe = "today" if intent == "READ_TODAYS_NOTES" else ("this week" if intent == "READ_WEEKS_NOTES" else entities.get("timeframe"))
        filter_tag = entities.get("filter")
        
        notes = NoteService.get_notes_by_filter(user_id, subject=subject, tag=filter_tag, timeframe=timeframe)
        if not notes and subject:
            # Try fuzzy topic / subject match
            notes = NoteService.get_notes_by_topic_or_subject(user_id, topic=subject)
        if not notes:
            # Fallback to recent notes for this user
            all_notes = NoteService.get_notes_by_filter(user_id)
            if all_notes:
                notes = all_notes[:15]

        if not notes:
            sub_label = f" for {subject}" if subject else ""
            spoken_response = f"No notes found{sub_label}. Say Note followed by your thoughts to record one."
            action = "none"
        else:
            first_note = notes[0]
            sub_label = f" for {subject}" if subject else ""
            spoken_response = f"Found {len(notes)} recent notes{sub_label}. Note 1 of {len(notes)}: {first_note['subject']}, {first_note['timestamp']}. {first_note['text']}. Say Next, Previous, Repeat, or Stop."
            action = "NAVIGATE_AUDIO_REVIEW"
            response_data = {"notes": notes, "current_index": 0, "subject_filter": subject or "All"}
            next_context.update({
                "current_mode": "audio_review",
                "review_notes": notes,
                "current_index": 0,
                "current_subject": subject or "All"
            })

    elif intent == "AUDIO_NEXT":
        mode = next_context.get("current_mode")
        if mode == "flashcard_active" or (next_context.get("flashcards") and mode not in ["quiz_active", "retrieval"]):
            cards = next_context.get("flashcards", [])
            if not cards:
                cards = FlashcardService.get_flashcards(user_id)
                if not cards:
                    cards = FlashcardService.generate_curriculum_flashcards("General")
                next_context["flashcards"] = cards
            
            curr_idx = next_context.get("current_card_index", 0)
            if curr_idx + 1 < len(cards):
                next_idx = curr_idx + 1
                next_context["current_card_index"] = next_idx
                next_context["is_card_flipped"] = False
                next_card = cards[next_idx]
                next_front = next_card.get("front") or next_card.get("question", "")
                spoken_response = f"Card {next_idx + 1} of {len(cards)}: {next_front}"
                action = "FLASHCARD_INDEX_UPDATED"
                response_data = {"current_index": next_idx, "is_flipped": False, "card": next_card}
            else:
                spoken_response = "You have reached the last flashcard. Say Flip, Explain, or Exit."
                action = "none"
                response_data = {"current_index": curr_idx, "is_flipped": False}
        elif mode == "quiz_active":
            quiz_items = next_context.get("quiz_items", [])
            curr_idx = next_context.get("current_quiz_index", 0)
            if curr_idx + 1 < len(quiz_items):
                next_idx = curr_idx + 1
                next_context["current_quiz_index"] = next_idx
                next_q = quiz_items[next_idx]
                spoken_response = f"Question {next_idx + 1} of {len(quiz_items)}: {next_q['question']}"
                action = "QUIZ_INDEX_UPDATED"
                response_data = {"current_index": next_idx}
            else:
                spoken_response = "You have reached the last question. Speak your answer or say Exit."
                action = "none"
        else:
            items = next_context.get("search_results" if mode == "retrieval" else "review_notes", [])
            curr_idx = next_context.get("current_index", 0)
            
            if not items:
                all_notes = NoteService.get_notes_by_filter(user_id)
                if all_notes:
                    items = all_notes
                    next_context["review_notes"] = items
                    next_context["current_index"] = 0
                    curr_idx = 0

            if not items:
                spoken_response = "No active audio list. Say Find my notes or Read today's notes to start."
            elif curr_idx + 1 < len(items):
                next_idx = curr_idx + 1
                next_context["current_index"] = next_idx
                item = items[next_idx]
                tag_intro = f"[{item['tag']}] " if item.get("tag") and item['tag'] != 'General' else ""
                spoken_response = f"Note {next_idx + 1} of {len(items)}: {item['subject']}, {item['timestamp']}. {tag_intro}{item['text']}."
                action = "AUDIO_INDEX_UPDATED"
                response_data = {"current_index": next_idx, "current_note": item}
            else:
                spoken_response = "You have reached the end of the notes. Say Previous, Repeat, or Exit."

    elif intent == "AUDIO_PREVIOUS":
        mode = next_context.get("current_mode")
        if mode == "flashcard_active" or (next_context.get("flashcards") and mode not in ["quiz_active", "retrieval"]):
            cards = next_context.get("flashcards", [])
            if not cards:
                cards = FlashcardService.get_flashcards(user_id)
                if not cards:
                    cards = FlashcardService.generate_curriculum_flashcards("General")
                next_context["flashcards"] = cards
            
            curr_idx = next_context.get("current_card_index", 0)
            if curr_idx > 0:
                prev_idx = curr_idx - 1
                next_context["current_card_index"] = prev_idx
                next_context["is_card_flipped"] = False
                prev_card = cards[prev_idx]
                prev_front = prev_card.get("front") or prev_card.get("question", "")
                spoken_response = f"Card {prev_idx + 1} of {len(cards)}: {prev_front}"
                action = "FLASHCARD_INDEX_UPDATED"
                response_data = {"current_index": prev_idx, "is_flipped": False, "card": prev_card}
            else:
                spoken_response = "You are at the first flashcard. Say Next or Flip."
                action = "none"
        elif mode == "quiz_active":
            quiz_items = next_context.get("quiz_items", [])
            curr_idx = next_context.get("current_quiz_index", 0)
            if curr_idx > 0:
                prev_idx = curr_idx - 1
                next_context["current_quiz_index"] = prev_idx
                prev_q = quiz_items[prev_idx]
                spoken_response = f"Question {prev_idx + 1} of {len(quiz_items)}: {prev_q['question']}"
                action = "QUIZ_INDEX_UPDATED"
                response_data = {"current_index": prev_idx}
            else:
                spoken_response = "You are at the first question. Speak your option letter or answer."
                action = "none"
        else:
            items = next_context.get("search_results" if mode == "retrieval" else "review_notes", [])
            curr_idx = next_context.get("current_index", 0)
            
            if not items:
                spoken_response = "No active audio list."
            elif curr_idx > 0:
                prev_idx = curr_idx - 1
                next_context["current_index"] = prev_idx
                item = items[prev_idx]
                tag_intro = f"[{item['tag']}] " if item.get("tag") and item['tag'] != 'General' else ""
                spoken_response = f"Note {prev_idx + 1} of {len(items)}: {item['subject']}, {item['timestamp']}. {tag_intro}{item['text']}."
                action = "AUDIO_INDEX_UPDATED"
                response_data = {"current_index": prev_idx, "current_note": item}
            else:
                spoken_response = "You are at the first note. Say Next or Repeat."

    elif intent == "AUDIO_REPEAT":
        mode = next_context.get("current_mode")
        if mode == "flashcard_active":
            cards = next_context.get("flashcards", [])
            curr_idx = next_context.get("current_card_index", 0)
            if cards and 0 <= curr_idx < len(cards):
                card = cards[curr_idx]
                front_text = card.get("front") or card.get("question", "")
                spoken_response = f"Repeating Card {curr_idx + 1} of {len(cards)}: {front_text} Speak your answer, or say Flip."
                action = "FLASHCARD_REPEAT"
                response_data = {"current_index": curr_idx}
            else:
                spoken_response = "No flashcard to repeat."
        elif mode == "quiz_active":
            quiz_items = next_context.get("quiz_items", [])
            curr_idx = next_context.get("current_quiz_index", 0)
            if quiz_items and 0 <= curr_idx < len(quiz_items):
                q = quiz_items[curr_idx]
                opt_str = ". ".join(q.get("options", [])) if q.get("options") else ""
                spoken_response = f"Repeating Question {curr_idx + 1}: {q['question']}. {opt_str}"
                action = "QUIZ_REPEAT"
                response_data = {"current_index": curr_idx}
            else:
                spoken_response = "No quiz question to repeat."
        else:
            items = next_context.get("search_results" if mode == "retrieval" else "review_notes", [])
            curr_idx = next_context.get("current_index", 0)
            
            if items and 0 <= curr_idx < len(items):
                item = items[curr_idx]
                tag_intro = f"[{item['tag']}] " if item.get("tag") and item['tag'] != 'General' else ""
                spoken_response = f"Repeating Note {curr_idx + 1} of {len(items)}: {item['subject']}, {item['timestamp']}. {tag_intro}{item['text']}."
                action = "AUDIO_REPEAT"
                response_data = {"current_index": curr_idx, "current_note": item}
            else:
                last_note = NoteService.get_last_note(user_id)
                if last_note:
                    spoken_response = f"Last note: {last_note['subject']}, {last_note['timestamp']}. {last_note['text']}."
                else:
                    spoken_response = "No note to repeat."

    elif intent == "AUDIO_STOP":
        spoken_response = "Stopped."
        action = "AUDIO_STOP"

    elif intent == "AUDIO_EXIT":
        spoken_response = "Exited to home screen."
        action = "NAVIGATE_HOME"
        next_context["current_mode"] = "home"

    elif intent == "HELP":
        spoken_response = (
            "Here are things you can say: "
            "Start Biology lecture. "
            "Note: Mitosis is cell division. "
            "Tag this as important. "
            "Correct decision to division. "
            "Find my notes about cell division. "
            "Read today's notes. "
            "Start flashcards. "
            "Quiz me on Biology. "
            "Bookmark this note. "
            "Where did I note photosynthesis? "
            "And say Stop at any time to interrupt speech."
        )
        action = "SHOW_HELP"

    # ---------------------------------------------------------------------
    # Flashcard Generation & Audio Revision (FLASHCARDS / START_FLASHCARDS)
    # ---------------------------------------------------------------------
    elif intent in ["FLASHCARDS", "START_FLASHCARDS"]:
        topic = entities.get("topic") or entities.get("subject")
        clean_topic = topic.strip().title() if topic else None
        flashcards_res = FlashcardService.generate_flashcards_from_topic(
            user_id, topic=clean_topic, gemini_service=gemini_service
        )
        if not flashcards_res or not flashcards_res.get("cards"):
            # Check multi-subject curriculum and Gemini dynamic generation
            gen_materials = AcademicKnowledgeService.generate_and_store_materials(
                user_id, topic=clean_topic or "General", gemini_service=gemini_service
            )
            if gen_materials and gen_materials.get("flashcards") and gen_materials["flashcards"].get("cards"):
                flashcards_res = gen_materials["flashcards"]

        if not flashcards_res or not flashcards_res.get("cards"):
            topic_str = f" for {clean_topic}" if clean_topic else ""
            spoken_response = f"No notes found{topic_str} to make flashcards. Record some lecture notes first."
            action = "none"
        else:
            cards = flashcards_res["cards"]
            topic_name = flashcards_res.get("topic", clean_topic or "your notes")
            first_card = cards[0]
            front_text = first_card.get("front") or first_card.get("question", "")
            spoken_response = f"Here are {len(cards)} flashcards on {topic_name}. Card 1: {front_text} Speak your answer, say Explain, or say Flip."
            action = "NAVIGATE_FLASHCARDS"
            response_data = {
                "type": "flashcards",
                "topic": topic_name,
                "flashcards": cards,
                "cards": cards,
                "current_index": 0
            }
            next_context.update({
                "current_mode": "flashcard_active",
                "flashcards": cards,
                "current_card_index": 0
            })

    elif intent in ["FLASHCARD_ANSWER", "FLASHCARD_DONT_KNOW", "FLASHCARD_EXPLAIN", "FLASHCARD_FLIP", "FLASHCARD_DIFFICULTY", "FLASHCARD_SKIP"]:
        cards = next_context.get("flashcards", [])
        curr_idx = next_context.get("current_card_index", 0)
        
        # Robust fallback if flashcards list is empty in context
        if not cards:
            cards = FlashcardService.get_flashcards(user_id)
            if not cards:
                cards = FlashcardService.generate_curriculum_flashcards("General")
            next_context["flashcards"] = cards
            next_context["current_card_index"] = curr_idx

        if not cards or curr_idx >= len(cards):
            spoken_response = "Flashcard session completed. Great job!"
            action = "NAVIGATE_HOME"
            next_context["current_mode"] = "home"
        else:
            card = cards[curr_idx]
            front_text = card.get("front") or card.get("question", "")
            back_text = card.get("back") or card.get("answer", "")
            currently_flipped = next_context.get("is_card_flipped", False)

            if intent in ["FLASHCARD_FLIP", "FLASHCARD_EXPLAIN", "FLASHCARD_DONT_KNOW"]:
                if currently_flipped and intent == "FLASHCARD_FLIP":
                    next_context["is_card_flipped"] = False
                    spoken_response = f"Flipped back to question: {front_text}."
                    action = "FLASHCARD_FLIP"
                    response_data = {"current_index": curr_idx, "is_flipped": False, "question": front_text}
                else:
                    next_context["is_card_flipped"] = True
                    spoken_response = f"The answer is: {back_text}. Say Easy, Medium, Hard, or Next to continue."
                    action = "FLASHCARD_FLIP"
                    response_data = {"current_index": curr_idx, "is_flipped": True, "answer": back_text}
            elif intent == "FLASHCARD_DIFFICULTY":
                diff = entities.get("difficulty", "Medium")
                if "id" in card:
                    FlashcardService.record_review(card["id"], is_correct=True, difficulty=diff)
                next_idx = curr_idx + 1
                if next_idx < len(cards):
                    next_context["current_card_index"] = next_idx
                    next_context["is_card_flipped"] = False
                    next_card = cards[next_idx]
                    next_front = next_card.get("front") or next_card.get("question", "")
                    spoken_response = f"Marked as {diff}. Next card: {next_front}"
                    action = "FLASHCARD_INDEX_UPDATED"
                    response_data = {"current_index": next_idx, "is_flipped": False, "card": next_card}
                else:
                    spoken_response = f"Marked as {diff}. You have completed all flashcards in this session!"
                    action = "FLASHCARDS_COMPLETED"
                    response_data = {"current_index": next_idx, "is_flipped": False}
                    next_context["current_mode"] = "home"
            elif intent == "FLASHCARD_SKIP":
                next_idx = curr_idx + 1
                if next_idx < len(cards):
                    next_context["current_card_index"] = next_idx
                    next_context["is_card_flipped"] = False
                    next_card = cards[next_idx]
                    next_front = next_card.get("front") or next_card.get("question", "")
                    spoken_response = f"Card {next_idx + 1} of {len(cards)}: {next_front}"
                    action = "FLASHCARD_INDEX_UPDATED"
                    response_data = {"current_index": next_idx, "is_flipped": False, "card": next_card}
                else:
                    spoken_response = "You reached the end of the flashcards. Say Exit or Restart to review again."
                    action = "FLASHCARDS_COMPLETED"
                    response_data = {"current_index": curr_idx, "is_flipped": False}
                    next_context["current_mode"] = "home"
            else: # FLASHCARD_ANSWER
                user_ans = entities.get("answer", text)
                eval_res = QuizService.evaluate_spoken_answer(
                    {"question": front_text, "expected_answer": back_text},
                    user_ans,
                    gemini_service=gemini_service
                )
                is_correct = eval_res["result"] == "Correct"
                if "id" in card:
                    FlashcardService.record_review(card["id"], is_correct=is_correct)
                
                next_idx = curr_idx + 1
                if next_idx < len(cards):
                    next_context["current_card_index"] = next_idx
                    next_context["is_card_flipped"] = False
                    next_card = cards[next_idx]
                    next_front = next_card.get("front") or next_card.get("question", "")
                    spoken_response = f"{eval_res['spoken_feedback']} Card {next_idx + 1}: {next_front}"
                    action = "FLASHCARD_INDEX_UPDATED"
                    response_data = {"current_index": next_idx, "is_flipped": False, "card": next_card, "evaluation": eval_res}
                else:
                    spoken_response = f"{eval_res['spoken_feedback']} That was the last card. Revision complete!"
                    action = "FLASHCARDS_COMPLETED"
                    response_data = {"current_index": next_idx, "is_flipped": False, "evaluation": eval_res}
                    next_context["current_mode"] = "home"

    # ---------------------------------------------------------------------
    # Quiz Generation & Exam Mode (QUIZ_ME / START_QUIZ / REVISE_WEAK_TOPICS)
    # ---------------------------------------------------------------------
    elif intent in ["QUIZ_ME", "START_QUIZ", "REVISE_WEAK_TOPICS"]:
        is_weak = intent == "REVISE_WEAK_TOPICS"
        topic = entities.get("topic") or entities.get("subject") or entities.get("filter")
        clean_topic = topic.strip().title() if topic else None
        timeframe = entities.get("timeframe")

        if is_weak:
            quiz_items = QuizService.generate_quiz(user_id, weak_topics_only=True)
            if not quiz_items:
                spoken_response = "No weak topics found. Great job on your previous quizzes!"
                action = "none"
            else:
                first_q = quiz_items[0]
                spoken_response = f"Starting weak topics revision with {len(quiz_items)} questions. Question 1: {first_q['question']} Speak your answer."
                action = "NAVIGATE_QUIZ"
                response_data = {"quiz_items": quiz_items, "questions": quiz_items, "current_index": 0}
                next_context.update({
                    "current_mode": "quiz_active",
                    "quiz_items": quiz_items,
                    "current_quiz_index": 0,
                    "quiz_score": 0,
                    "quiz_answers": []
                })
        else:
            quiz_res = QuizService.generate_mcq_quiz_from_topic(
                user_id, topic=clean_topic, gemini_service=gemini_service
            )
            if not quiz_res or not quiz_res.get("questions"):
                # Check multi-subject curriculum and Gemini dynamic generation
                gen_materials = AcademicKnowledgeService.generate_and_store_materials(
                    user_id, topic=clean_topic or "General", gemini_service=gemini_service
                )
                if gen_materials and gen_materials.get("quiz") and gen_materials["quiz"].get("questions"):
                    quiz_res = gen_materials["quiz"]

            if not quiz_res or not quiz_res.get("questions"):
                topic_str = f" for {clean_topic}" if clean_topic else ""
                spoken_response = f"No notes found{topic_str}."
                action = "none"
            else:
                questions = quiz_res["questions"]
                topic_name = quiz_res.get("topic", clean_topic or "your notes")
                first_q = questions[0]
                opt_preview = f" Option A: {first_q['options'][0]} Option B: {first_q['options'][1]}" if first_q.get("options") and len(first_q["options"]) >= 2 else ""
                spoken_response = f"Here are {len(questions)} quiz questions on {topic_name}. Question 1: {first_q['question']}.{opt_preview}. Speak your option letter or answer."
                action = "NAVIGATE_QUIZ"
                response_data = {
                    "type": "quiz",
                    "topic": topic_name,
                    "questions": questions,
                    "quiz_items": questions,
                    "current_index": 0
                }
                next_context.update({
                    "current_mode": "quiz_active",
                    "quiz_items": questions,
                    "current_quiz_index": 0,
                    "quiz_score": 0,
                    "quiz_answers": []
                })

    elif intent == "QUIZ_ANSWER":
        quiz_items = next_context.get("quiz_items", [])
        curr_idx = next_context.get("current_quiz_index", 0)
        score_so_far = next_context.get("quiz_score", 0)
        
        if not quiz_items or curr_idx >= len(quiz_items):
            spoken_response = "Quiz is already finished."
            action = "NAVIGATE_HOME"
            next_context["current_mode"] = "home"
        else:
            q_item = quiz_items[curr_idx]
            user_ans = entities.get("answer", text).strip()
            
            # Check MCQ letter match (e.g. "A", "B", "C", "D" or "Option B")
            correct_letter = q_item.get("correct_answer", "").strip().upper()
            user_clean = user_ans.upper().replace("OPTION", "").replace("CHOICE", "").replace("ANSWER", "").strip()
            
            if correct_letter and user_clean in ["A", "B", "C", "D"]:
                if user_clean == correct_letter:
                    eval_res = {
                        "result": "Correct",
                        "score": 1.0,
                        "feedback": f"Correct! Option {correct_letter} is the right answer.",
                        "spoken_feedback": f"Correct! Option {correct_letter} is right."
                    }
                else:
                    eval_res = {
                        "result": "Incorrect",
                        "score": 0.0,
                        "feedback": f"Incorrect. The correct answer was Option {correct_letter}.",
                        "spoken_feedback": f"Incorrect. Option {correct_letter} was the correct answer."
                    }
            else:
                eval_res = QuizService.evaluate_spoken_answer(q_item, user_ans, gemini_service=gemini_service)
            
            # Record in DB
            QuizService.record_quiz_answer(user_id, q_item, user_ans, eval_res)
            
            new_score = score_so_far + eval_res["score"]
            next_context["quiz_score"] = new_score
            
            next_idx = curr_idx + 1
            if next_idx < len(quiz_items):
                next_context["current_quiz_index"] = next_idx
                next_q = quiz_items[next_idx]
                spoken_response = f"{eval_res['spoken_feedback']} Question {next_idx + 1}: {next_q['question']}"
                action = "QUIZ_ANSWER_EVALUATED"
                response_data = {
                    "evaluation": eval_res,
                    "next_index": next_idx,
                    "score": new_score,
                    "selected_option": user_clean if user_clean in ["A", "B", "C", "D"] else None
                }
            else:
                total_q = len(quiz_items)
                weaks = QuizService.get_weak_topics(user_id)
                weak_rec = f" You should revise {weaks[0]['topic']}." if weaks else " Excellent mastery of your notes!"
                spoken_response = f"{eval_res['spoken_feedback']} Quiz complete! You scored {int(new_score)} out of {total_q}.{weak_rec}"
                action = "QUIZ_COMPLETED"
                response_data = {
                    "final_score": new_score,
                    "total": total_q,
                    "evaluation": eval_res,
                    "selected_option": user_clean if user_clean in ["A", "B", "C", "D"] else None
                }
                next_context["current_mode"] = "home"

    # ---------------------------------------------------------------------
    # Bookmarks
    # ---------------------------------------------------------------------
    elif intent == "BOOKMARK_NOTE":
        res = BookmarkService.add_bookmark(user_id, note_id=next_context.get("last_note_id"))
        spoken_response = res["message"]
        action = "BOOKMARK_ADDED"
        response_data = res

    elif intent == "READ_BOOKMARKS":
        bms = BookmarkService.get_bookmarks(user_id)
        if not bms:
            spoken_response = "You don't have any bookmarks saved."
        else:
            spoken_response = f"You have {len(bms)} bookmarks. Bookmark 1: {bms[0]['subject']}, {bms[0]['text']}. Say Next to hear more."
            action = "NAVIGATE_RETRIEVAL"
            response_data = {"bookmarks": bms}
            next_context.update({
                "current_mode": "retrieval",
                "search_results": bms,
                "current_index": 0
            })

    # ---------------------------------------------------------------------
    # Extended Phase 4.5: Timeline / Memory Map Queries
    # ---------------------------------------------------------------------
    elif intent == "TIMELINE_TOPIC_QUERY":
        topic = entities.get("query", "")
        res = TimelineService.query_topic_time(user_id, topic)
        spoken_response = res["speech"]
        response_data = res

    elif intent == "TIMELINE_TIME_QUERY":
        time_q = entities.get("time", "")
        res = TimelineService.query_notes_around_time(user_id, time_q)
        spoken_response = res["speech"]
        response_data = res

    elif intent == "TIMELINE_TOPICS_SUMMARY":
        res = TimelineService.get_today_topics_summary(user_id)
        spoken_response = res["speech"]
        response_data = res

    return jsonify({
        "intent": intent,
        "raw_text": text,
        "spoken_response": spoken_response,
        "action": action,
        "data": response_data,
        "context": next_context
    })

# =========================================================================
# Direct REST Endpoints for UI and Integration
# =========================================================================

@app.route("/api/notes", methods=["GET", "POST"])
def notes_endpoint():
    if request.method == "POST":
        data = request.get_json() or {}
        user_id = data.get("user_id", DEFAULT_USER_ID)
        text = data.get("text", "")
        subject = data.get("subject")
        session_id = data.get("session_id")
        explicit_tag = data.get("tag")
        confidence = float(data.get("confidence", 1.0))
        
        note = NoteService.create_note(user_id, text, subject, session_id, explicit_tag, confidence)
        return jsonify(note), 201

    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    subject = request.args.get("subject")
    tag = request.args.get("tag")
    timeframe = request.args.get("timeframe")
    notes = NoteService.get_notes_by_filter(user_id, subject, tag, timeframe)
    return jsonify(notes)

@app.route("/api/notes/last", methods=["GET"])
def get_last_note_endpoint():
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    session_id = request.args.get("session_id")
    note = NoteService.get_last_note(user_id, session_id)
    if not note:
        return jsonify({"message": "No notes found"}), 404
    return jsonify(note)

@app.route("/api/notes/<note_id>/history", methods=["GET"])
def note_history_endpoint(note_id):
    history = CorrectionService.get_correction_history(note_id)
    return jsonify(history)

@app.route("/api/notes/<note_id>", methods=["DELETE"])
def delete_note_endpoint(note_id):
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    success = NoteService.delete_note(note_id, user_id)
    if success:
        return jsonify({"success": True, "message": "Note deleted successfully.", "note_id": note_id}), 200
    return jsonify({"error": "Note not found or already deleted."}), 404

@app.route("/api/sessions/active", methods=["GET"])
def get_active_session_endpoint():
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    session = NoteService.get_active_session(user_id)
    if not session:
        return jsonify({"is_active": False, "session": None})
    return jsonify({"is_active": True, "session": session})

@app.route("/api/sessions/start", methods=["POST"])
def start_session_endpoint():
    data = request.get_json() or {}
    user_id = data.get("user_id", DEFAULT_USER_ID)
    subject = data.get("subject", "General")
    session = NoteService.start_session(user_id, subject)
    return jsonify(session)

@app.route("/api/sessions/end", methods=["POST"])
def end_session_endpoint():
    data = request.get_json() or {}
    user_id = data.get("user_id", DEFAULT_USER_ID)
    session = NoteService.end_active_session(user_id)
    if not session:
        return jsonify({"message": "No active session to end"}), 400
    return jsonify(session)

@app.route("/api/search", methods=["GET"])
def search_endpoint():
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    q = request.args.get("q", "")
    results = SearchService.search_notes(user_id, q)
    return jsonify(results)

@app.route("/api/analytics", methods=["GET"])
def analytics_endpoint():
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    analytics = NoteService.get_analytics(user_id)
    res = dict(analytics)
    res["success"] = True
    res["analytics"] = analytics
    return jsonify(res), 200

@app.route("/api/bookmarks", methods=["GET", "POST"])
def bookmarks_endpoint():
    if request.method == "POST":
        data = request.get_json() or {}
        user_id = data.get("user_id", DEFAULT_USER_ID)
        note_id = data.get("note_id")
        label = data.get("label")
        res = BookmarkService.add_bookmark(user_id, note_id, label)
        return jsonify(res)
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    bms = BookmarkService.get_bookmarks(user_id)
    return jsonify(bms)

@app.route("/api/flashcards", methods=["GET"])
def flashcards_endpoint():
    user_id = request.args.get("user_id", DEFAULT_USER_ID)
    subject = request.args.get("subject")
    cards = FlashcardService.get_flashcards(user_id, subject)
    return jsonify(cards)

@app.route("/api/quiz/generate", methods=["POST"])
def generate_quiz_endpoint():
    data = request.get_json() or {}
    user_id = data.get("user_id", DEFAULT_USER_ID)
    topic = data.get("topic")
    quiz_res = QuizService.generate_mcq_quiz_from_topic(user_id, topic=topic, gemini_service=gemini_service)
    if not quiz_res or not quiz_res.get("questions"):
        gen_data = AcademicKnowledgeService.generate_and_store_materials(user_id, topic or "General", gemini_service=gemini_service)
        if gen_data and gen_data.get("quiz") and gen_data["quiz"].get("questions"):
            quiz_res = gen_data["quiz"]
    if not quiz_res or not quiz_res.get("questions"):
        quiz_res = QuizService.generate_mcq_quiz_from_topic(user_id, topic=None, gemini_service=gemini_service)

    if not quiz_res or not quiz_res.get("questions"):
        return jsonify({
            "error": "No notes found in database to generate quiz.",
            "type": "quiz",
            "topic": topic or "General",
            "questions": []
        }), 404
    return jsonify(quiz_res), 200

@app.route("/api/flashcards/generate", methods=["POST"])
def generate_flashcards_endpoint():
    data = request.get_json() or {}
    user_id = data.get("user_id", DEFAULT_USER_ID)
    topic = data.get("topic")
    flashcards_res = FlashcardService.generate_flashcards_from_topic(user_id, topic=topic, gemini_service=gemini_service)
    if not flashcards_res or not flashcards_res.get("cards"):
        gen_data = AcademicKnowledgeService.generate_and_store_materials(user_id, topic or "General", gemini_service=gemini_service)
        if gen_data and gen_data.get("flashcards") and gen_data["flashcards"].get("cards"):
            flashcards_res = gen_data["flashcards"]
    if not flashcards_res or not flashcards_res.get("cards"):
        flashcards_res = FlashcardService.generate_flashcards_from_topic(user_id, topic=None, gemini_service=gemini_service)

    if not flashcards_res or not flashcards_res.get("cards"):
        return jsonify({
            "error": "No notes found in database to generate flashcards.",
            "type": "flashcards",
            "topic": topic or "General",
            "cards": []
        }), 404
    return jsonify(flashcards_res), 200

@app.route("/api/settings/gemini_key", methods=["GET", "POST"])
def gemini_key_settings():
    if request.method == "POST":
        data = request.get_json() or {}
        key = data.get("api_key", "").strip()
        success = gemini_service.set_api_key(key)
        return jsonify({
            "success": success,
            "gemini_available": gemini_service.is_available(),
            "message": "Gemini API key configured successfully." if success else "Failed to initialize Gemini with provided key."
        }), (200 if success else 400)
    else:
        return jsonify({
            "gemini_available": gemini_service.is_available(),
            "has_key": bool(gemini_service.api_key)
        }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
