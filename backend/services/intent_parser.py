import re
from typing import Dict, Any, Optional

class IntentParser:
    """
    Two-tier intent parsing engine:
    1. Deterministic Regex Pattern Matcher (Primary - fast, predictable, handles all core syntax)
    2. Gemini API LLM Fallback (Secondary - for complex natural phrasing or ambiguous utterances)
    """

    def __init__(self, gemini_service=None):
        self.gemini_service = gemini_service
        self._init_patterns()

    def _init_patterns(self):
        # Compiled regex patterns for high performance and clean matching
        self.patterns = [
            # Core Lecture Lifecycle
            (
                r"^(?:please\s+)?(?:start|begin|open)\s+(?:the\s+)?(?P<subject>.+?)\s+(?:lecture|class|session)\.?$",
                "START_LECTURE"
            ),
            (
                r"^(?:please\s+)?(?:start|begin|record|create)\s+(?:the\s+)?(?P<subject>(?!recent\b|recents\b).+?)\s+notes?\.?$",
                "START_LECTURE"
            ),
            (
                r"^(?:please\s+)?(?:start|begin)\s+(?:a\s+)?(?:new\s+)?notes?\s+(?:for|on|about|in)\s+(?P<subject>.+?)\.?$",
                "START_LECTURE"
            ),
            (
                r"^(?:please\s+)?(?:start|begin)\s+(?:a\s+)?(?:new\s+)?(?P<subject>biology|geography|computer\s+science|physics|chemistry|mathematics|history)(?:\s+(?:lecture|class|session|notes?))?\.?$",
                "START_LECTURE"
            ),
            (
                r"^(?:please\s+)?(?:end|finish|stop|close|complete|exit|done\s+with)\s+(?:the\s+)?(?:lecture|class|session|recording)\.?$",
                "END_LECTURE"
            ),

            # Note Creation with explicit prefix
            (
                r"^(?:please\s+)?(?:take\s+a\s+note|record|note)(?:\s*:\s*|\s+that\s+|\s+)(?P<content>.+)$",
                "CREATE_NOTE"
            ),

            # Tagging Commands (checks all permutations of mark/tag/label [this/it/last note/this note] [as/to] [a/an] [tag])
            (
                r"^(?:please\s+)?(?:tag|mark|set|label)(?:\s+(?:this\s+note|the\s+last\s+note|last\s+note|this|the\s+note|note|it))?(?:\s+as|\s+to)?(?:\s+(?:a|an))?\s+(?P<tag>definition|example|important|general|exam\s+point|key\s+point|key\s+concept|exam\s+note|formula)\.?$",
                "TAG_NOTE"
            ),

            # Correction Commands
            (
                r"^(?:please\s+)?(?:correct|change|replace)\s+(?:the\s+word\s+)?(?P<target>.+?)\s+(?:to|with)\s+(?P<replacement>.+?)\.?$",
                "CORRECT_NOTE_REPLACE"
            ),
            # "Correct the last note to [new full content]" or "Correct last note: [new full content]"
            (
                r"^(?:please\s+)?(?:correct|edit)\s+(?:the\s+)?last\s+note(?:\s*:\s*|\s+to\s+)(?P<new_content>.+)$",
                "CORRECT_NOTE_FULL"
            ),
            (
                r"^(?:please\s+)?(?:correct|edit)\s+(?:the\s+)?last\s+note\.?$",
                "CORRECT_LAST_NOTE_PROMPT"
            ),

            # Deletion of captured notes
            (
                r"^(?:please\s+)?(?:delete|remove|discard|erase|drop)\s+(?:the\s+)?(?:last\s+note|that\s+note|wrong\s+note|note)\.?$",
                "DELETE_NOTE"
            ),
            (
                r"^(?:please\s+)?(?:delete|remove|discard|erase)\s+note\s+(?P<note_id>\S+)\.?$",
                "DELETE_NOTE"
            ),

            # Open Recents Navigation
            (
                r"^(?:please\s+)?(?:open|show|go to|view|launch)\s+(?:the\s+|my\s+)?(?:recents?|recent\s+notes?|recent\s+recordings?)(?:\s+(?:tab|screen|page))?\.?$",
                "OPEN_RECENTS"
            ),
            (
                r"^(?:please\s+)?(?:recents?|recent\s+notes?|recent\s+recordings?)\s+(?:tab|screen|page)\.?$",
                "OPEN_RECENTS"
            ),
            (
                r"^(?:please\s+)?(?:recents|recent\s+recordings)\.?$",
                "OPEN_RECENTS"
            ),

            # Study Analytics & Visual Graphs Navigation
            (
                r"^(?:please\s+)?(?:open|show|view|go to|display)\s+(?:the\s+|my\s+)?(?:analytics|study analytics|progress|stats|statistics|visual\s+graphs?|visual\s+charts?|graphs?|charts?)(?:\s+(?:tab|screen|page))?\.?$",
                "OPEN_ANALYTICS"
            ),
            (
                r"^(?:please\s+)?(?:analytics|study analytics|my progress|my stats|study stats|visual\s+graphs?|visual\s+charts?|show graphs|show charts|show graph|show chart)\.?$",
                "OPEN_ANALYTICS"
            ),

            # Open Search / Voice Retrieval Navigation
            (
                r"^(?:please\s+)?(?:open|show|go to|view|launch)\s+(?:the\s+)?(?:search|search notes|search tab|voice search|voice retrieval|retrieval)\.?$",
                "OPEN_SEARCH"
            ),
            (
                r"^(?:please\s+)?(?:search notes|search my notes|find notes)\.?$",
                "OPEN_SEARCH"
            ),
            (
                r"^(?:please\s+)?search\.?$",
                "OPEN_SEARCH"
            ),

            # Search & Targeted Retrieval
            (
                r"^(?:please\s+)?(?:retrieve|fetch|find|get|search|look up)\s+(?:the\s+)?(?P<query>.+?)\s+notes?\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:retrieve|fetch)\s+(?:the\s+)?(?P<query>(?!notes\b|recents\b|recent\b|lecture\b|flashcards?\b|quiz\b).+?)\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:find|search|show|get|retrieve|look up)(?: my)? notes (?:about|on|regarding|for|in)\s+(?P<query>.+?)\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:search for|search|find|look up)\s+(?:my\s+)?notes\s+(?:about|on|regarding|for|in)\s+(?P<query>.+?)\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:search for|search|find|look up)\s+(?P<query>(?!notes\b|recents\b|recent\b|lecture\b|flashcards?\b|quiz\b).+?)\s+in (?:my\s+)?notes\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:notes (?:about|on|regarding|for))\s+(?P<query>.+?)\.?$",
                "SEARCH_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:search for|search|find|look up)\s+(?P<query>(?!notes\b|recents\b|recent\b|lecture\b|flashcards?\b|quiz\b).+?)\.?$",
                "SEARCH_NOTES"
            ),

            # Read / Audio Skim & Recent Notes
            (
                r"^(?:please\s+)?(?:read|play|show|get|list)\s+(?:all\s+)?(?:my\s+)?recent\s+notes(?:\s+(?:for|in|on|about)\s+(?P<subject>.+?))?\.?$",
                "READ_RECENT_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:read|play|show|get|list)\s+(?:all\s+)?(?:my\s+)?recent\s+(?P<subject>.+?)\s+notes\.?$",
                "READ_RECENT_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:read|play|show|get|list)\s+(?:all\s+)?(?:my\s+)?recents(?:\s+(?:for|in|on|about)\s+(?P<subject>.+?))?\.?$",
                "READ_RECENT_NOTES"
            ),
            (
                r"^(?:please\s+)?(?:recent\s+notes|recents)(?:\s+(?:for|in|on|about)\s+(?P<subject>.+?))?\.?$",
                "READ_RECENT_NOTES"
            ),
            (
                r"^(?:please\s+)?read (?:today's|todays)\s+(?:(?P<subject>.+?)\s+)?notes\.?$",
                "READ_TODAYS_NOTES"
            ),
            (
                r"^(?:please\s+)?read (?:this week's|this weeks)\s+(?:(?P<subject>.+?)\s+)?notes\.?$",
                "READ_WEEKS_NOTES"
            ),
            (
                r"^(?:please\s+)?read (?:all\s+)?(?:my\s+)?(?P<subject>(?!recent\b).+?)\s+notes\.?$",
                "READ_SUBJECT_NOTES"
            ),
            (
                r"^(?:please\s+)?play (?:all\s+)?(?P<filter>.+?)\s+notes(?: from (?P<timeframe>today|this week))?\.?$",
                "AUDIO_SKIM"
            ),

            # Audio Navigation Controls
            (r"^(?:please\s+)?(?:next|next note|next card|go forward|forward|skip|continue)\.?$", "AUDIO_NEXT"),
            (r"^(?:please\s+)?(?:previous|prev|previous note|previous card|go back|back)\.?$", "AUDIO_PREVIOUS"),
            (r"^(?:please\s+)?(?:repeat|repeat note|repeat card|again|replay)\.?$", "AUDIO_REPEAT"),
            (r"^(?:please\s+)?(?:stop|pause|quiet|hush|silence|halt)\.?$", "AUDIO_STOP"),
            (r"^(?:please\s+)?(?:resume|continue|keep playing)\.?$", "AUDIO_RESUME"),
            (r"^(?:please\s+)?(?:exit|back|leave|done|quit)\.?$", "AUDIO_EXIT"),
            (r"^(?:please\s+)?(?:help|what can i say|instructions)\.?$", "HELP"),

            # Flashcard Generation & Revision (FLASHCARDS)
            (
                r"^(?:please\s+)?(?:give\s+me|make|create|generate|show|get|open|view|start)\s+(?:audio\s+)?flashcards?\s+(?:on|for|about)\s+(?P<topic>.+?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?(?:give\s+me|make|create|generate|show|get|open|view|start)\s+(?:audio\s+)?flashcards?\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?flashcards?\s+(?:on|for|about)\s+(?P<topic>.+?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?flashcards?\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?(?:study\s+)?cards?\s+(?:on|for|about)\s+(?P<topic>.+?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?(?:study\s+)?cards?\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?(?:start\s+(?:audio\s+)?flashcards?(?:\s+revision)?|revise\s+flashcards?)\s+(?:for|on|about)\s+(?P<topic>.+?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?(?:start\s+(?:audio\s+)?flashcards?(?:\s+revision)?|revise\s+flashcards?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?start\s+(?:audio\s+)?revision\s+(?:for|on|about)\s+(?P<topic>.+?)\.?$",
                "FLASHCARDS"
            ),
            (
                r"^(?:please\s+)?start\s+(?:audio\s+)?revision\.?$",
                "FLASHCARDS"
            ),
            (r"^(?:please\s+)?(?:skip|next card|next|skip card)\.?$", "FLASHCARD_SKIP"),
            (r"^(?:please\s+)?(?:i don't know|i dont know|dont know|pass)\.?$", "FLASHCARD_DONT_KNOW"),
            (r"^(?:please\s+)?(?:explain|explain this|why|more details|details)\.?$", "FLASHCARD_EXPLAIN"),
            (r"^(?:please\s+)?(?:flip|flip card|flip the card|turn|turn card|turn over|turn the card|show answer|reveal answer|reveal|what is the answer|answer|ground truth)\.?$", "FLASHCARD_FLIP"),

            # Quiz Generation & Exam Mode (QUIZ_ME)
            (
                r"^(?:please\s+)?(?:quiz|test)\s+(?:me\s+)?(?:on|about|for)?\s*(?P<topic>geography|biology|physics|chemistry|computer\s+science|mathematics|history)(?:\s+notes?)?\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?P<topic>geography|biology|physics|chemistry|computer\s+science|mathematics|history)\s+(?:quiz|test)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:give\s+me|start|take)\s+(?:a\s+)?(?P<topic>geography|biology|physics|chemistry|computer\s+science|mathematics|history)\s+(?:quiz|test)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:quiz|test)\s+me\s+(?:on|about)\s+(?:(?:all\s+)?my\s+)?(?P<subject>.+?)\s+notes(?:\s+from\s+(?P<timeframe>today|this\s+week))?\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:quiz|test)\s+(?:me\s+)?(?:on|about)\s+(?P<topic>.+?)(?:\s+from\s+(?P<timeframe>today|this\s+week))?\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:quiz|test)\s+me(?:\s+from\s+(?P<timeframe>today|this\s+week))?\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:start\s+(?:a\s+)?quiz|exam\s+mode|take\s+(?:a\s+)?quiz|give\s+me\s+(?:a\s+)?quiz|practice\s+quiz)\s+(?:for|on|about)\s+(?P<topic>.+?)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:start\s+(?:a\s+)?quiz|exam\s+mode|take\s+(?:a\s+)?quiz|give\s+me\s+(?:a\s+)?quiz|practice\s+quiz)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:quiz|quizzes|questions)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?(?:test\s+me|test)\.?$",
                "QUIZ_ME"
            ),
            (
                r"^(?:please\s+)?revise\s+(?:my\s+)?weak\s+topics?\.?$",
                "REVISE_WEAK_TOPICS"
            ),

            # Extended 4.4: Bookmarks
            (
                r"^(?:please\s+)?(?:bookmark(?:\s+(?:this|this\s+note|the\s+note|note|it))?|save(?:\s+as)?\s+bookmark|add(?:\s+a)?\s+bookmark|mark\s+this\s+for\s+revision|important\s+exam\s+point|exam\s+bookmark)\.?$",
                "BOOKMARK_NOTE"
            ),
            (
                r"^(?:please\s+)?(?:read|show|list|get) (?:my\s+)?bookmarks\.?$",
                "READ_BOOKMARKS"
            ),
            (
                r"^(?:please\s+)?revise (?:my\s+)?exam points\.?$",
                "READ_BOOKMARKS"
            ),

            # Extended 4.5: Timeline / Memory Map
            (
                r"^(?:where|when) did i (?:note|mention|write about|talk about)\s+(?P<query>.+?)\??$",
                "TIMELINE_TOPIC_QUERY"
            ),
            (
                r"^what did i (?:note|write|record) around\s+(?P<time>.+?)\??$",
                "TIMELINE_TIME_QUERY"
            ),
            (
                r"^what topics did i cover today\??$",
                "TIMELINE_TOPICS_SUMMARY"
            ),

            # Extended 4.6: Contextual / Fuzzy Search
            (
                r"^find (?:the )?(?:example|formula|definition|note) (?:my professor gave|where i wrote|about)\s+(?P<query>.+?)\.?$",
                "CONTEXTUAL_SEARCH"
            )
        ]

    def parse(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses spoken text into structured intent and entity dict.
        Returns: {
            "intent": str,
            "entities": dict,
            "confidence": float,
            "raw_text": str,
            "source": "regex" | "gemini" | "fallback_dictation"
        }
        """
        if not text or not text.strip():
            return {
                "intent": "UNKNOWN",
                "entities": {},
                "confidence": 0.0,
                "raw_text": "",
                "source": "regex"
            }

        cleaned = text.strip()
        # Apply intelligent speech auto-correction
        try:
            from services.auto_correction_service import AutoSpeechCorrectionService
            auto_fixed, _ = AutoSpeechCorrectionService.correct_transcript(cleaned, gemini_service=self.gemini_service, context=context)
            if auto_fixed:
                cleaned = auto_fixed.strip()
        except Exception:
            pass

        # Normalize punctuation and casing for regex match, keeping raw text intact
        normalized = cleaned.lower().rstrip(".?!")

        # 1. Check Regex Patterns First
        for pattern, intent_name in self.patterns:
            match = re.match(pattern, normalized, re.IGNORECASE)
            if match:
                entities = match.groupdict()
                # Clean entities
                cleaned_entities = {}
                for k, v in entities.items():
                    if v:
                        cleaned_entities[k] = v.strip()
                
                # If CREATE_NOTE, extract content preserving original casing if possible
                if intent_name == "CREATE_NOTE" and "content" in cleaned_entities:
                    # Extract from raw cleaned text to preserve capitalization
                    note_match = re.match(r"^(?:please\s+)?(?:take\s+a\s+note|record|note)(?:\s*:\s*|\s+that\s+|\s+)(.+)$", cleaned, re.IGNORECASE)
                    if note_match:
                        cleaned_entities["content"] = note_match.group(1).strip()

                # If SEARCH_NOTES, clean extra prepositions from query
                if intent_name == "SEARCH_NOTES" and "query" in cleaned_entities:
                    q_val = cleaned_entities["query"]
                    q_val = re.sub(r"^(?:about|on|regarding|for|in)\s+", "", q_val, flags=re.IGNORECASE).strip()
                    q_val = re.sub(r"\s+in (?:my\s+)?notes$", "", q_val, flags=re.IGNORECASE).strip()
                    cleaned_entities["query"] = q_val

                # Normalize tag names to Title case (Important, Definition, Example, General)
                if "tag" in cleaned_entities:
                    tag_val = cleaned_entities["tag"].lower()
                    if "import" in tag_val or "exam" in tag_val or "key" in tag_val:
                        cleaned_entities["tag"] = "Important"
                    elif "def" in tag_val:
                        cleaned_entities["tag"] = "Definition"
                    elif "examp" in tag_val:
                        cleaned_entities["tag"] = "Example"
                    else:
                        cleaned_entities["tag"] = "General"

                return {
                    "intent": intent_name,
                    "entities": cleaned_entities,
                    "confidence": 1.0,
                    "raw_text": cleaned,
                    "source": "regex"
                }

        # 2. Context-dependent shorthands
        if context:
            mode = context.get("current_mode")
            if mode == "flashcard_active":
                # If answering flashcard or giving difficulty
                if normalized in ["1", "easy", "simple", "it was easy"]:
                    return {"intent": "FLASHCARD_DIFFICULTY", "entities": {"difficulty": "Easy"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["2", "medium", "normal", "moderate"]:
                    return {"intent": "FLASHCARD_DIFFICULTY", "entities": {"difficulty": "Medium"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["3", "hard", "difficult", "tough"]:
                    return {"intent": "FLASHCARD_DIFFICULTY", "entities": {"difficulty": "Hard"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["flip", "flip card", "flip the card", "turn", "turn card", "turn over", "turn the card", "show answer", "reveal", "reveal answer", "what is the answer", "answer", "ground truth"]:
                    return {"intent": "FLASHCARD_FLIP", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["next", "next card", "skip", "forward", "go forward", "continue", "skip card"]:
                    return {"intent": "FLASHCARD_SKIP", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["previous", "prev", "previous card", "back", "go back"]:
                    return {"intent": "AUDIO_PREVIOUS", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["repeat", "repeat card", "again", "replay"]:
                    return {"intent": "AUDIO_REPEAT", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["exit", "stop", "done", "quit", "leave", "finish"]:
                    return {"intent": "AUDIO_EXIT", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["explain", "explain this", "why", "more details", "details"]:
                    return {"intent": "FLASHCARD_EXPLAIN", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                else:
                    return {"intent": "FLASHCARD_ANSWER", "entities": {"answer": cleaned}, "confidence": 0.9, "raw_text": cleaned, "source": "regex"}
            elif mode == "quiz_active":
                # Check option letter shorthand (A, B, C, D, Option A, Choice A, etc.)
                opt_match = re.match(r"^(?:option|choice|answer)?\s*([a-d])\.?$", normalized)
                if opt_match:
                    letter = opt_match.group(1).upper()
                    return {"intent": "QUIZ_ANSWER", "entities": {"answer": f"Option {letter}"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                if normalized in ["first", "first option"]:
                    return {"intent": "QUIZ_ANSWER", "entities": {"answer": "Option A"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["second", "second option"]:
                    return {"intent": "QUIZ_ANSWER", "entities": {"answer": "Option B"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["third", "third option"]:
                    return {"intent": "QUIZ_ANSWER", "entities": {"answer": "Option C"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["fourth", "fourth option"]:
                    return {"intent": "QUIZ_ANSWER", "entities": {"answer": "Option D"}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                return {"intent": "QUIZ_ANSWER", "entities": {"answer": cleaned}, "confidence": 0.9, "raw_text": cleaned, "source": "regex"}
            elif mode == "retrieval":
                if normalized in ["next", "next note", "skip", "forward", "go forward", "continue"]:
                    return {"intent": "AUDIO_NEXT", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["previous", "prev", "previous note", "back", "go back"]:
                    return {"intent": "AUDIO_PREVIOUS", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["repeat", "repeat note", "again", "replay"]:
                    return {"intent": "AUDIO_REPEAT", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["stop", "pause", "quiet", "silence", "halt"]:
                    return {"intent": "AUDIO_STOP", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["exit", "done", "quit", "leave", "home"]:
                    return {"intent": "AUDIO_EXIT", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                elif normalized in ["help", "what can i say", "instructions"]:
                    return {"intent": "HELP", "entities": {}, "confidence": 1.0, "raw_text": cleaned, "source": "regex"}
                else:
                    # Clean out any leading search preambles
                    clean_q = re.sub(r"^(?:please\s+)?(?:search for|search|find|look up|notes about|notes on)\s+", "", cleaned, flags=re.IGNORECASE).strip()
                    clean_q = re.sub(r"\s+in (?:my\s+)?notes$", "", clean_q, flags=re.IGNORECASE).strip()
                    if clean_q:
                        return {"intent": "SEARCH_NOTES", "entities": {"query": clean_q}, "confidence": 0.95, "raw_text": cleaned, "source": "regex"}
            elif mode == "active_lecture" and not normalized.startswith("note"):
                pass

        # 3. Gemini Fallback for Ambiguous / Natural Input
        if self.gemini_service and self.gemini_service.is_available():
            gemini_result = self.gemini_service.parse_intent(cleaned, context)
            if gemini_result and gemini_result.get("intent") != "UNKNOWN":
                return gemini_result

        # 4. Default / Fallback: If in active lecture, treat as note dictation if it doesn't match commands
        if context and context.get("current_session_id") and len(cleaned.split()) >= 3:
            command_starters = (
                "start ", "begin ", "open ", "create ", "end ", "finish ", "stop ", "exit ",
                "retrieve ", "fetch ", "search ", "find ", "look up ", "delete ", "remove ",
                "erase ", "discard ", "read ", "play ", "quiz ", "flashcard ", "help"
            )
            if not any(normalized.startswith(cmd) for cmd in command_starters):
                return {
                    "intent": "CREATE_NOTE",
                    "entities": {"content": cleaned},
                    "confidence": 0.75,
                    "raw_text": cleaned,
                    "source": "fallback_dictation"
                }

        return {
            "intent": "UNKNOWN",
            "entities": {},
            "confidence": 0.0,
            "raw_text": cleaned,
            "source": "regex"
        }
