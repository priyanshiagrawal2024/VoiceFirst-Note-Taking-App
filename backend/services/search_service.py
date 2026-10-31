import re
from typing import Dict, Any, List, Optional
from database import get_db_connection

class SearchService:
    STOP_WORDS = {"about", "on", "regarding", "for", "in", "the", "a", "an", "my", "notes", "note", "all", "please", "me", "find", "search", "show", "get"}

    @classmethod
    def _calculate_relevance(cls, query: str, note: Dict[str, Any]) -> float:
        text_lower = note["text"].lower()
        subject_lower = note["subject"].lower()
        tag_lower = note["tag"].lower()
        query_lower = query.lower().strip()
        
        if not query_lower:
            return 1.0

        score = 0.0
        
        # Exact phrase match in note text
        if query_lower in text_lower:
            score += 10.0
        # Exact phrase match in subject (e.g. searching "Biology" or "Geography")
        if query_lower in subject_lower:
            score += 12.0

        # Token matches
        query_words = set(re.findall(r"\w+", query_lower))
        text_words = set(re.findall(r"\w+", text_lower))
        subject_words = set(re.findall(r"\w+", subject_lower))

        # Filter out common filler words for semantic matching
        meaningful_words = {w for w in query_words if w not in cls.STOP_WORDS}
        if not meaningful_words:
            meaningful_words = query_words

        # Common word matches
        common_text = meaningful_words.intersection(text_words)
        common_subj = meaningful_words.intersection(subject_words)
        
        score += len(common_text) * 2.5
        score += len(common_subj) * 3.0

        # Substring/prefix token matches (e.g. "algorithm" matches "algorithms")
        for qw in meaningful_words:
            if len(qw) >= 4:
                if any(qw in tw or tw in qw for tw in text_words if len(tw) >= 4):
                    score += 1.5
                if any(qw in sw or sw in qw for sw in subject_words if len(sw) >= 4):
                    score += 2.0

        # Tag priority boost ONLY if there was an actual match
        if score > 0:
            if tag_lower == "important":
                score += 1.5
            elif tag_lower == "definition":
                score += 1.2

        return score

    @classmethod
    def search_notes(cls, user_id: str, query: str) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notes 
            WHERE user_id = ? AND is_deleted = 0
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        cleaned_q = (query or "").strip()
        if not cleaned_q or cleaned_q.lower() in ["all", "*"]:
            # Return all active notes
            return [dict(r) for r in rows]
        
        scored_notes = []
        for r in rows:
            note_dict = dict(r)
            score = cls._calculate_relevance(cleaned_q, note_dict)
            if score > 0:
                note_dict["relevance_score"] = score
                scored_notes.append(note_dict)

        # Sort by highest relevance score first, then newest
        scored_notes.sort(key=lambda x: (x["relevance_score"], x["created_at"]), reverse=True)
        return scored_notes

    @classmethod
    def format_search_speech(cls, results: List[Dict[str, Any]], query: str, index: int = 0) -> str:
        total = len(results)
        q_clean = (query or "").strip()
        q_label = f" about {q_clean}" if q_clean and q_clean.lower() not in ["all", "*"] else ""

        if total == 0:
            return f"I couldn't find any notes{q_label}."
        
        current = results[index]
        note_num = index + 1
        tag_intro = f"[{current['tag']}] " if current.get("tag") and current['tag'] != "General" else ""
        
        if total == 1:
            return f"Found 1 note{q_label}. {current['subject']}, {current['timestamp']}. {tag_intro}{current['text']}. Say Repeat, or Exit."
        
        return f"Found {total} notes{q_label}. Note {note_num} of {total}: {current['subject']}, {current['timestamp']}. {tag_intro}{current['text']}. Say Next, Previous, or Repeat."
