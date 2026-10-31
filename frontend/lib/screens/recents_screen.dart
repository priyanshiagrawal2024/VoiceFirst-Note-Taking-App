import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/theme.dart';
import '../core/models/note_model.dart';
import '../core/services/voice_commander.dart';
import '../providers/notes_provider.dart';
import '../widgets/accessible_widgets.dart';

class RecentsScreen extends StatefulWidget {
  const RecentsScreen({super.key});

  @override
  State<RecentsScreen> createState() => _RecentsScreenState();
}

class _RecentsScreenState extends State<RecentsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final voiceCommander = context.read<VoiceCommander>();
      final notesProvider = context.read<NotesProvider>();
      voiceCommander.dialogueManager.currentMode = "recents";
      notesProvider.fetchNotes();
      // Only speak screen intro if voice commander isn't already speaking the navigation announcement
      if (!voiceCommander.isSpeaking) {
        voiceCommander.ttsService.speak(
          "Recent recordings screen. You have ${notesProvider.notes.length} total notes. Tap any note to listen, filter by subject, or tap the delete button to remove wrong notes.",
        );
      }
    });
  }

  @override
  void dispose() {
    try {
      final voiceCommander = context.read<VoiceCommander>();
      voiceCommander.dialogueManager.currentMode = "home";
    } catch (_) {}
    super.dispose();
  }

  Future<void> _confirmDeleteNote(BuildContext context, NoteModel note) async {
    final notesProvider = context.read<NotesProvider>();
    final voiceCommander = context.read<VoiceCommander>();

    // Audio prompt
    voiceCommander.ttsService.speak("Confirm deletion. Are you sure you want to delete this note?");

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AccessibleTheme.surfaceElevated,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AccessibleTheme.errorRed, width: 2),
        ),
        title: Row(
          children: const [
            Icon(Icons.delete_forever, color: AccessibleTheme.errorRed, size: 28),
            SizedBox(width: 10),
            Text(
              "Delete Note?",
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Subject: ${note.subject}",
              style: const TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              "\"${note.text}\"",
              style: const TextStyle(color: Colors.white, fontSize: 15),
            ),
            const SizedBox(height: 12),
            const Text(
              "This action will permanently delete this captured note.",
              style: TextStyle(color: Colors.white70, fontSize: 13),
            ),
          ],
        ),
        actions: [
          AccessibleButton(
            label: "Cancel",
            icon: Icons.close,
            isPrimary: false,
            onPressed: () => Navigator.pop(ctx, false),
          ),
          AccessibleButton(
            label: "Delete",
            icon: Icons.delete,
            isDestructive: true,
            onPressed: () => Navigator.pop(ctx, true),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      final success = await notesProvider.deleteNote(note.noteId);
      if (success) {
        voiceCommander.ttsService.speak("Note deleted successfully.");
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: AccessibleTheme.surfaceElevated,
              content: Text("Deleted note from ${note.subject}"),
              duration: const Duration(seconds: 2),
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesProvider = context.watch<NotesProvider>();
    final voiceCommander = context.watch<VoiceCommander>();

    final recentNotes = notesProvider.filteredRecentNotes;
    final subjects = notesProvider.availableSubjects;
    final selectedSubject = notesProvider.selectedSubject;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Recent Notes",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22, color: AccessibleTheme.primaryGold),
        ),
        backgroundColor: AccessibleTheme.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white, size: 28),
            tooltip: "Refresh notes",
            onPressed: () => notesProvider.fetchNotes(),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Voice Waveform & Microphone Status
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: AccessibleTheme.surface,
              child: Center(
                child: VoiceWaveformIndicator(
                  state: voiceCommander.state,
                  onMicTap: () {
                    if (voiceCommander.isListening) {
                      voiceCommander.stopListening();
                    } else if (voiceCommander.isSpeaking) {
                      voiceCommander.interruptSpeech();
                    } else {
                      voiceCommander.startListening();
                    }
                  },
                ),
              ),
            ),

            // Header Banner
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AccessibleTheme.surfaceElevated,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.mic, color: Color(0xFFE53935), size: 28),
                      SizedBox(width: 8),
                      Text(
                        "RECENTS",
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white24, width: 1),
                    ),
                    child: Text(
                      "${recentNotes.length} ${recentNotes.length == 1 ? 'Recording' : 'Recordings'}",
                      style: const TextStyle(fontSize: 13, color: Colors.white70, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ),

            // Subject Category Horizontal Filter Pills
            Container(
              padding: const EdgeInsets.symmetric(vertical: 10),
              color: AccessibleTheme.surface,
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: subjects.map((subj) {
                    final isSelected = subj.toLowerCase() == selectedSubject.toLowerCase();
                    final count = subj == "All"
                        ? notesProvider.recentNotes.length
                        : notesProvider.recentNotes.where((n) => n.subject.toLowerCase() == subj.toLowerCase()).length;
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: Semantics(
                        button: true,
                        selected: isSelected,
                        label: "Filter $subj notes, $count items",
                        child: InkWell(
                          borderRadius: BorderRadius.circular(20),
                          onTap: () {
                            notesProvider.setSubjectFilter(subj);
                          },
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                            decoration: BoxDecoration(
                              color: isSelected ? AccessibleTheme.primaryGold : AccessibleTheme.surfaceElevated,
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: isSelected ? Colors.white : Colors.white24,
                                width: 1.5,
                              ),
                            ),
                            child: Row(
                              children: [
                                Text(
                                  subj,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.bold,
                                    color: isSelected ? Colors.black : Colors.white,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: isSelected ? Colors.black.withOpacity(0.2) : Colors.white.withOpacity(0.12),
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    "$count",
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                      color: isSelected ? Colors.black : Colors.white70,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
            ),

            // Recents Notes List View
            Expanded(
              child: recentNotes.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.mic_none, size: 56, color: Colors.white38),
                            const SizedBox(height: 14),
                            Text(
                              "No recordings found for $selectedSubject.",
                              style: const TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              "Say \"Note: [content]\" or start a lecture session to capture notes.",
                              style: TextStyle(fontSize: 15, color: Colors.white70),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      itemCount: recentNotes.length,
                      itemBuilder: (context, index) {
                        final note = recentNotes[index];
                        final isPlaying = notesProvider.isNotePlaying(note) && voiceCommander.isSpeaking;
                        final words = note.text.trim().split(RegExp(r'\s+')).length;
                        final durationSec = (words * 0.45).ceil().clamp(1, 180);
                        final durationStr = "${durationSec ~/ 60}:${(durationSec % 60).toString().padLeft(2, '0')}";

                        return Semantics(
                          container: true,
                          label:
                              "Note from ${note.subject}. ${note.text}. Timestamp: ${note.timestamp}. Double tap to listen. Delete button available.",
                          child: Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                              side: BorderSide(
                                color: isPlaying ? AccessibleTheme.primaryGold : Colors.white12,
                                width: isPlaying ? 2.5 : 1.2,
                              ),
                            ),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(14),
                              onTap: () {
                                if (isPlaying) {
                                  voiceCommander.interruptSpeech();
                                  notesProvider.setCurrentlyPlayingNoteId(null);
                                } else {
                                  notesProvider.setCurrentlyPlayingNoteId(note.noteId);
                                  voiceCommander.ttsService.speak(
                                    "Reading note for ${note.subject}. Tagged as ${note.tag}. Content: ${note.text}.",
                                  );
                                }
                              },
                              child: Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.center,
                                  children: [
                                    // Left Circular Play Button (iOS Voice Memos crimson styling)
                                    Semantics(
                                      button: true,
                                      label: isPlaying ? "Pause audio for ${note.subject}" : "Play audio for ${note.subject}",
                                      child: Container(
                                        width: 48,
                                        height: 48,
                                        decoration: BoxDecoration(
                                          shape: BoxShape.circle,
                                          color: isPlaying
                                              ? AccessibleTheme.primaryGold.withOpacity(0.2)
                                              : const Color(0xFFE53935).withOpacity(0.15),
                                          border: Border.all(
                                            color: isPlaying ? AccessibleTheme.primaryGold : const Color(0xFFE53935),
                                            width: 2,
                                          ),
                                        ),
                                        child: Icon(
                                          isPlaying ? Icons.pause : Icons.play_arrow,
                                          color: isPlaying ? AccessibleTheme.primaryGold : const Color(0xFFE53935),
                                          size: 28,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 14),

                                    // Note Details
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            children: [
                                              TagBadge(tag: note.tag),
                                              const SizedBox(width: 8),
                                              Text(
                                                note.subject.toUpperCase(),
                                                style: const TextStyle(
                                                  color: AccessibleTheme.primaryGold,
                                                  fontSize: 12,
                                                  fontWeight: FontWeight.bold,
                                                  letterSpacing: 0.5,
                                                ),
                                              ),
                                              const Spacer(),
                                              Text(
                                                note.timestamp,
                                                style: const TextStyle(fontSize: 12, color: Colors.white54),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 6),
                                          Text(
                                            note.text,
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            style: const TextStyle(
                                              fontSize: 16,
                                              fontWeight: FontWeight.w600,
                                              color: Colors.white,
                                              height: 1.25,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Row(
                                            children: [
                                              Text(
                                                durationStr,
                                                style: const TextStyle(fontSize: 12, color: Colors.white54, fontWeight: FontWeight.bold),
                                              ),
                                              if (isPlaying) ...[
                                                const SizedBox(width: 8),
                                                const Icon(Icons.graphic_eq, color: AccessibleTheme.primaryGold, size: 16),
                                              ],
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),

                                    const SizedBox(width: 10),

                                    // Right Delete Action Button
                                    Semantics(
                                      button: true,
                                      label: "Delete note: ${note.text}",
                                      child: IconButton(
                                        icon: const Icon(Icons.delete_outline, color: AccessibleTheme.errorRed, size: 28),
                                        tooltip: "Delete Note",
                                        onPressed: () => _confirmDeleteNote(context, note),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
