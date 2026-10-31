import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/theme.dart';
import '../core/services/voice_commander.dart';
import '../providers/notes_provider.dart';
import '../widgets/accessible_widgets.dart';

class VoiceRetrievalScreen extends StatefulWidget {
  const VoiceRetrievalScreen({super.key});

  @override
  State<VoiceRetrievalScreen> createState() => _VoiceRetrievalScreenState();
}

class _VoiceRetrievalScreenState extends State<VoiceRetrievalScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final voiceCommander = context.read<VoiceCommander>();
      final notesProvider = context.read<NotesProvider>();
      voiceCommander.dialogueManager.currentMode = "retrieval";

      _searchController.text = notesProvider.searchQuery;

      if (notesProvider.searchResults.isEmpty) {
        notesProvider.performSearch("");
        voiceCommander.ttsService.speak(
          "Voice retrieval screen. Say 'Find my notes about' followed by a topic, or type in the search bar.",
        );
      } else {
        final q = notesProvider.searchQuery;
        voiceCommander.ttsService.speak(
          "Showing ${notesProvider.searchResults.length} notes${q.isNotEmpty ? ' for ' + q : ''}. Tap any note to listen, or say Next.",
        );
      }
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _executeSearch(BuildContext context, String query) {
    final voiceCommander = context.read<VoiceCommander>();
    final notesProvider = context.read<NotesProvider>();
    final cleanQ = query.trim();
    if (cleanQ.isNotEmpty) {
      voiceCommander.processUtterance("search $cleanQ");
    } else {
      notesProvider.performSearch("");
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesProvider = context.watch<NotesProvider>();
    final voiceCommander = context.watch<VoiceCommander>();

    final results = notesProvider.searchResults;
    final currentIndex = notesProvider.searchIndex;
    final query = notesProvider.searchQuery;

    // Keep controller synced if query updated via voice
    if (query.isNotEmpty && _searchController.text != query) {
      _searchController.text = query;
      _searchController.selection = TextSelection.fromPosition(
        TextPosition(offset: _searchController.text.length),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Search & Voice Retrieval",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22, color: AccessibleTheme.primaryGold),
        ),
        backgroundColor: AccessibleTheme.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white, size: 28),
            tooltip: "Reset search",
            onPressed: () {
              _searchController.clear();
              notesProvider.performSearch("");
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Accessible Search Bar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AccessibleTheme.surfaceElevated,
              child: Row(
                children: [
                  Expanded(
                    child: Semantics(
                      label: "Search notes by keyword or subject",
                      textField: true,
                      child: TextField(
                        controller: _searchController,
                        style: const TextStyle(color: Colors.white, fontSize: 17),
                        decoration: InputDecoration(
                          hintText: "Search notes (e.g. Mitosis, Newton)...",
                          hintStyle: const TextStyle(color: Colors.white54, fontSize: 15),
                          prefixIcon: const Icon(Icons.search, color: AccessibleTheme.primaryGold, size: 24),
                          suffixIcon: _searchController.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear, color: Colors.white70),
                                  onPressed: () {
                                    _searchController.clear();
                                    notesProvider.performSearch("");
                                  },
                                )
                              : null,
                          filled: true,
                          fillColor: Colors.black45,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: Colors.white24, width: 1.5),
                          ),
                          focusedBorder: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(12),
                            borderSide: const BorderSide(color: AccessibleTheme.primaryGold, width: 2.5),
                          ),
                        ),
                        onSubmitted: (val) => _executeSearch(context, val),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Search submit icon button
                  Semantics(
                    button: true,
                    label: "Submit search",
                    child: Container(
                      decoration: BoxDecoration(
                        color: AccessibleTheme.accentBlue.withOpacity(0.25),
                        shape: BoxShape.circle,
                        border: Border.all(color: AccessibleTheme.accentBlue, width: 1.5),
                      ),
                      child: IconButton(
                        icon: const Icon(Icons.search, color: AccessibleTheme.accentBlue, size: 26),
                        tooltip: "Search",
                        onPressed: () => _executeSearch(context, _searchController.text),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Voice Search Mic button
                  Semantics(
                    button: true,
                    label: voiceCommander.isListening ? "Stop microphone" : "Voice search microphone",
                    child: Container(
                      decoration: BoxDecoration(
                        color: voiceCommander.isListening
                            ? AccessibleTheme.errorRed
                            : AccessibleTheme.primaryGold,
                        shape: BoxShape.circle,
                      ),
                      child: IconButton(
                        icon: Icon(
                          voiceCommander.isListening ? Icons.mic : Icons.mic_none,
                          color: Colors.black,
                          size: 26,
                        ),
                        tooltip: "Speak query",
                        onPressed: () {
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
                ],
              ),
            ),

            // Status & Count Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              color: Colors.black26,
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      query.isNotEmpty ? "RESULTS FOR \"$query\"" : "ALL NOTES",
                      style: const TextStyle(
                        color: AccessibleTheme.primaryGold,
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        letterSpacing: 0.8,
                      ),
                    ),
                  ),
                  Text(
                    results.isEmpty
                        ? "0 notes"
                        : "${currentIndex + 1} of ${results.length} notes",
                    style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),

            // Search Results List
            Expanded(
              child: results.isEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.search_off, size: 56, color: AccessibleTheme.tagImportant),
                            const SizedBox(height: 16),
                            Text(
                              query.isNotEmpty ? "No notes found for \"$query\"." : "No notes found.",
                              style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                              textAlign: TextAlign.center,
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              "Say \"Find my notes about [topic]\" or type a different keyword.",
                              style: TextStyle(fontSize: 15, color: Colors.white70),
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      itemCount: results.length,
                      itemBuilder: (context, index) {
                        final note = results[index];
                        final isSelected = index == currentIndex;
                        final isPlaying = notesProvider.isNotePlaying(note) && voiceCommander.isSpeaking;

                        return Semantics(
                          selected: isSelected,
                          container: true,
                          label:
                              "${isSelected ? 'Selected note. ' : ''}Note ${index + 1} of ${results.length}. ${note.subject}. ${note.text}. Timestamp: ${note.timestamp}. Double tap to listen.",
                          child: Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                              side: BorderSide(
                                color: isPlaying
                                    ? AccessibleTheme.primaryGold
                                    : (isSelected ? AccessibleTheme.accentBlue : Colors.white12),
                                width: isPlaying ? 2.5 : (isSelected ? 2.0 : 1.2),
                              ),
                            ),
                            child: InkWell(
                              borderRadius: BorderRadius.circular(14),
                              onTap: () {
                                notesProvider.setSearchIndex(index);
                                if (isPlaying) {
                                  voiceCommander.interruptSpeech();
                                  notesProvider.setCurrentlyPlayingNoteId(null);
                                } else {
                                  notesProvider.setCurrentlyPlayingNoteId(note.noteId);
                                  voiceCommander.ttsService.speak(
                                    "Note ${index + 1} of ${results.length}: ${note.subject}. Tagged as ${note.tag}. ${note.text}.",
                                  );
                                }
                              },
                              child: Padding(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.center,
                                  children: [
                                    // Circular Play/Pause Button
                                    Semantics(
                                      button: true,
                                      label: isPlaying ? "Pause audio" : "Play note",
                                      child: Container(
                                        width: 46,
                                        height: 46,
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
                                          size: 26,
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
                                            maxLines: 3,
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyle(
                                              fontSize: 16,
                                              fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                              color: Colors.white,
                                              height: 1.3,
                                            ),
                                          ),
                                          if (isPlaying) ...[
                                            const SizedBox(height: 6),
                                            const Row(
                                              children: [
                                                Icon(Icons.graphic_eq, color: AccessibleTheme.primaryGold, size: 16),
                                                SizedBox(width: 6),
                                                Text(
                                                  "Reading note aloud...",
                                                  style: TextStyle(color: AccessibleTheme.primaryGold, fontSize: 12, fontWeight: FontWeight.bold),
                                                ),
                                              ],
                                            ),
                                          ],
                                        ],
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

            // Accessible Audio Navigation Toolbar
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AccessibleTheme.surface,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  AccessibleButton(
                    label: "Previous",
                    icon: Icons.skip_previous,
                    isPrimary: false,
                    onPressed: () => voiceCommander.processUtterance("Previous."),
                  ),
                  AccessibleButton(
                    label: "Repeat",
                    icon: Icons.replay,
                    isPrimary: true,
                    onPressed: () => voiceCommander.processUtterance("Repeat."),
                  ),
                  AccessibleButton(
                    label: "Next",
                    icon: Icons.skip_next,
                    isPrimary: false,
                    onPressed: () => voiceCommander.processUtterance("Next."),
                  ),
                  AccessibleButton(
                    label: "Stop",
                    icon: Icons.stop,
                    isDestructive: true,
                    onPressed: () => voiceCommander.processUtterance("Stop."),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
