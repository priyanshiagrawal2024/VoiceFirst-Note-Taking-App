import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from database import get_db_connection

class NoteService:
    @staticmethod
    def classify_tag(text: str, explicit_tag: Optional[str] = None) -> str:
        if explicit_tag:
            tag_lower = explicit_tag.lower()
            if "import" in tag_lower:
                return "Important"
            elif "def" in tag_lower:
                return "Definition"
            elif "examp" in tag_lower:
                return "Example"
            elif "gen" in tag_lower:
                return "General"

        # Heuristic Auto-Tagging
        text_lower = text.lower()
        if any(w in text_lower for w in ["is defined as", "refers to", "the process of", "is the process", "is when", "means", "is a term for"]):
            return "Definition"
        if any(w in text_lower for w in ["for example", "for instance", "e.g.", "such as", "an example of"]):
            return "Example"
        if any(w in text_lower for w in ["important", "remember", "crucial", "essential", "key point", "exam point", "must know", "critical"]):
            return "Important"
        return "General"

    @classmethod
    def start_session(cls, user_id: str, subject: str) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Deactivate any previous active session
        now = datetime.now().isoformat()
        cursor.execute("UPDATE sessions SET is_active = 0, end_time = ? WHERE user_id = ? AND is_active = 1", (now, user_id))
        
        session_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO sessions (session_id, user_id, subject, start_time, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (session_id, user_id, subject.title(), now, now))
        
        conn.commit()
        conn.close()
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "subject": subject.title(),
            "start_time": now,
            "is_active": True
        }

    @classmethod
    def get_active_session(cls, user_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE user_id = ? AND is_active = 1 ORDER BY start_time DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def end_active_session(cls, user_id: str) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE user_id = ? AND is_active = 1 ORDER BY start_time DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        session = dict(row)
        now = datetime.now().isoformat()
        cursor.execute("UPDATE sessions SET is_active = 0, end_time = ? WHERE session_id = ?", (now, session["session_id"]))
        
        cursor.execute("SELECT COUNT(*) as count FROM notes WHERE session_id = ? AND is_deleted = 0", (session["session_id"],))
        count = cursor.fetchone()["count"]
        
        conn.commit()
        conn.close()
        session["note_count"] = count
        session["end_time"] = now
        session["is_active"] = False
        return session

    @classmethod
    def create_note(cls, user_id: str, text: str, subject: Optional[str] = None, 
                    session_id: Optional[str] = None, explicit_tag: Optional[str] = None, 
                    confidence: float = 1.0) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from services.auto_correction_service import AutoSpeechCorrectionService
        detected_subj = AutoSpeechCorrectionService.detect_subject(text, fallback_subject=None)

        # If subject/session_id not provided, check active session or detect from text
        if not session_id or not subject:
            active = cls.get_active_session(user_id)
            if active:
                session_id = session_id or active["session_id"]
                subject = subject or active["subject"]
            else:
                subject = subject or detected_subj or "General"

        # Cross-Domain Intelligence:
        # If the note content is clearly about a different recognized subject domain (e.g. Geography or Computer Science)
        # while the current session/subject is different (e.g. Biology):
        if detected_subj and subject and detected_subj.lower() != subject.lower():
            text_lower = text.lower()
            detected_lower = detected_subj.lower()
            starts_with_detected = (
                text_lower.startswith(detected_lower) or 
                text_lower.startswith(f"in {detected_lower}") or
                text_lower.startswith(f"for {detected_lower}") or
                text_lower.startswith(f"about {detected_lower}")
            )
            current_kws = AutoSpeechCorrectionService.DOMAIN_KEYWORDS.get(subject.title(), [])
            has_current_kws = any(kw in text_lower for kw in current_kws)

            if starts_with_detected or not has_current_kws:
                # Re-attribute note to detected subject domain
                subject = detected_subj
                # Decouple note from active session of different subject
                active = cls.get_active_session(user_id)
                if active and active.get("subject", "").lower() != detected_subj.lower():
                    session_id = None

        tag = cls.classify_tag(text, explicit_tag)
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()
        timestamp_display = now_dt.strftime("%I:%M %p") # e.g. "10:42 AM"
        note_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO notes (note_id, user_id, session_id, subject, text, tag, timestamp, confidence, created_at, updated_at, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (note_id, user_id, session_id, subject.title(), text, tag, timestamp_display, confidence, now_iso, now_iso))
        
        conn.commit()
        conn.close()
        
        return {
            "note_id": note_id,
            "user_id": user_id,
            "session_id": session_id,
            "subject": subject.title(),
            "text": text,
            "tag": tag,
            "timestamp": timestamp_display,
            "confidence": confidence,
            "created_at": now_iso,
            "updated_at": now_iso
        }

    @classmethod
    def get_last_note(cls, user_id: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        if session_id:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE user_id = ? AND session_id = ? AND is_deleted = 0 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, session_id))
        else:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE user_id = ? AND is_deleted = 0 
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def update_tag(cls, note_id: str, new_tag: str) -> Optional[Dict[str, Any]]:
        normalized_tag = cls.classify_tag("", explicit_tag=new_tag)
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE notes 
            SET tag = ?, updated_at = ? 
            WHERE note_id = ? AND is_deleted = 0
        """, (normalized_tag, now, note_id))
        
        cursor.execute("SELECT * FROM notes WHERE note_id = ?", (note_id,))
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        return dict(row) if row else None

    @classmethod
    def delete_note(cls, note_id: str, user_id: Optional[str] = None) -> bool:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        if user_id:
            cursor.execute("""
                UPDATE notes 
                SET is_deleted = 1, updated_at = ? 
                WHERE note_id = ? AND user_id = ? AND is_deleted = 0
            """, (now, note_id, user_id))
        else:
            cursor.execute("""
                UPDATE notes 
                SET is_deleted = 1, updated_at = ? 
                WHERE note_id = ? AND is_deleted = 0
            """, (now, note_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    @classmethod
    def get_notes_by_filter(cls, user_id: str, subject: Optional[str] = None, 
                            tag: Optional[str] = None, timeframe: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM notes WHERE user_id = ? AND is_deleted = 0"
        params = [user_id]
        
        if subject and subject.lower() != "all":
            query += " AND LOWER(subject) = ?"
            params.append(subject.lower())
            
        if tag and tag.lower() != "all":
            # Can be multiple tags e.g. "important and definition"
            tags_to_check = []
            for t in ["Definition", "Example", "Important", "General"]:
                if t.lower() in tag.lower():
                    tags_to_check.append(t)
            if tags_to_check:
                placeholders = ",".join("?" for _ in tags_to_check)
                query += f" AND tag IN ({placeholders})"
                params.extend(tags_to_check)
                
        if timeframe:
            tf = timeframe.lower()
            now = datetime.now()
            if "today" in tf:
                start_of_day = datetime(now.year, now.month, now.day).isoformat()
                query += " AND created_at >= ?"
                params.append(start_of_day)
            elif "week" in tf:
                start_of_week = (now - timedelta(days=7)).isoformat()
                query += " AND created_at >= ?"
                params.append(start_of_week)
                
        query += " ORDER BY created_at ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_notes_by_topic_or_subject(cls, user_id: str, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clean topic string from conversational prepositions and filler words
        clean_topic = ""
        if topic:
            clean_topic = topic.strip().lower()
            clean_topic = re.sub(r"^(?:on|about|for|regarding|in)\s+", "", clean_topic)
            clean_topic = re.sub(r"\s+(?:notes|lecture|class|session|revision)$", "", clean_topic)
            clean_topic = clean_topic.replace("my ", "").strip()

        if not clean_topic or clean_topic in ["all", "everything", "my notes", "notes", "lecture"]:
            active = cls.get_active_session(user_id)
            if active:
                cursor.execute("""
                    SELECT * FROM notes 
                    WHERE user_id = ? AND session_id = ? AND is_deleted = 0 
                    ORDER BY created_at ASC
                """, (user_id, active["session_id"]))
                rows = cursor.fetchall()
                if rows:
                    conn.close()
                    return [dict(r) for r in rows]

            cursor.execute("""
                SELECT * FROM notes 
                WHERE user_id = ? AND is_deleted = 0 
                ORDER BY created_at ASC
            """, (user_id,))
            rows = cursor.fetchall()
            if not rows and not user_id:
                # Check if notes exist under default student or any user only when no user_id specified
                cursor.execute("SELECT * FROM notes WHERE is_deleted = 0 ORDER BY created_at ASC")
                rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]

        # Targeted query with cleaned topic
        cursor.execute("""
            SELECT * FROM notes 
            WHERE user_id = ? AND is_deleted = 0 AND (
                LOWER(subject) = ? OR 
                LOWER(subject) LIKE ? OR 
                LOWER(text) LIKE ?
            )
            ORDER BY created_at ASC
        """, (user_id, clean_topic, f"%{clean_topic}%", f"%{clean_topic}%"))
        rows = cursor.fetchall()

        # If no notes for this user, only check cross-user if user_id is empty or None
        if not rows and not user_id:
            cursor.execute("""
                SELECT * FROM notes 
                WHERE is_deleted = 0 AND (
                    LOWER(subject) = ? OR 
                    LOWER(subject) LIKE ? OR 
                    LOWER(text) LIKE ?
                )
                ORDER BY created_at ASC
            """, (clean_topic, f"%{clean_topic}%", f"%{clean_topic}%"))
            rows = cursor.fetchall()

        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def get_analytics(cls, user_id: str) -> Dict[str, Any]:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Total notes
        cursor.execute("SELECT COUNT(*) as total FROM notes WHERE user_id = ? AND is_deleted = 0", (user_id,))
        total_notes = cursor.fetchone()["total"]

        # Fallback to all notes if user_id has no notes yet (e.g. cross-demo)
        if total_notes == 0:
            cursor.execute("SELECT COUNT(*) as total FROM notes WHERE is_deleted = 0")
            total_notes = cursor.fetchone()["total"]
            cursor.execute("""
                SELECT subject, COUNT(*) as count 
                FROM notes 
                WHERE is_deleted = 0 
                GROUP BY subject 
                ORDER BY count DESC
            """)
            subject_rows = cursor.fetchall()
            subject_counts = {r["subject"]: r["count"] for r in subject_rows}

            cursor.execute("""
                SELECT tag, COUNT(*) as count 
                FROM notes 
                WHERE is_deleted = 0 
                GROUP BY tag
            """)
            tag_rows = cursor.fetchall()
            tag_counts = {r["tag"]: r["count"] for r in tag_rows}

            cursor.execute("SELECT COUNT(*) as total FROM sessions")
            total_sessions = cursor.fetchone()["total"]
        else:
            # 2. Subject breakdown
            cursor.execute("""
                SELECT subject, COUNT(*) as count 
                FROM notes 
                WHERE user_id = ? AND is_deleted = 0 
                GROUP BY subject 
                ORDER BY count DESC
            """, (user_id,))
            subject_rows = cursor.fetchall()
            subject_counts = {r["subject"]: r["count"] for r in subject_rows}

            # 3. Tag breakdown
            cursor.execute("""
                SELECT tag, COUNT(*) as count 
                FROM notes 
                WHERE user_id = ? AND is_deleted = 0 
                GROUP BY tag
            """, (user_id,))
            tag_rows = cursor.fetchall()
            tag_counts = {r["tag"]: r["count"] for r in tag_rows}

            # 4. Total sessions
            cursor.execute("SELECT COUNT(*) as total FROM sessions WHERE user_id = ?", (user_id,))
            total_sessions = cursor.fetchone()["total"]

        conn.close()

        top_subjects = list(subject_counts.items())
        subj_summary = ", ".join(f"{count} in {subj}" for subj, count in top_subjects[:3]) if top_subjects else "no subject notes yet"
        important_count = tag_counts.get("Important", 0)
        definition_count = tag_counts.get("Definition", 0)
        example_count = tag_counts.get("Example", 0)
        general_count = tag_counts.get("General", 0)

        spoken_summary = (
            f"Study analytics summary: You have {total_notes} total notes across {len(subject_counts)} subjects, "
            f"including {subj_summary}. "
            f"You have {important_count} important exam points, {definition_count} definitions, and {example_count} examples recorded."
        )

        # Knowledge concept nodes for visual knowledge map
        concept_nodes = []
        for subj, count in top_subjects:
            percentage = round((count / max(total_notes, 1)) * 100, 1)
            concept_nodes.append({
                "subject": subj,
                "notes_count": count,
                "percentage": percentage,
            })

        return {
            "total_notes": total_notes,
            "total_sessions": total_sessions,
            "subject_counts": subject_counts,
            "tag_counts": tag_counts,
            "top_subjects": top_subjects,
            "concept_nodes": concept_nodes,
            "spoken_summary": spoken_summary
        }
