import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/theme.dart';
import '../core/services/voice_commander.dart';
import '../providers/notes_provider.dart';
import '../widgets/accessible_widgets.dart';

class FlashcardsScreen extends StatefulWidget {
  const FlashcardsScreen({super.key});

  @override
  State<FlashcardsScreen> createState() => _FlashcardsScreenState();
}

class _FlashcardsScreenState extends State<FlashcardsScreen> {
  int _lastSpokenIndex = -1;
  bool _lastSpokenFlipped = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final voiceCommander = context.read<VoiceCommander>();
      voiceCommander.dialogueManager.currentMode = "flashcard_active";
      _initCards();
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

  Future<void> _initCards() async {
    final notesProvider = context.read<NotesProvider>();
    final voiceCommander = context.read<VoiceCommander>();

    voiceCommander.dialogueManager.currentMode = "flashcard_active";

    if (notesProvider.flashcards.isEmpty && !notesProvider.isLoadingFlashcards) {
      voiceCommander.ttsService.speak("Loading audio flashcards from your lecture notes...");
      await notesProvider.loadFlashcards();
    }

    if (mounted) {
      voiceCommander.dialogueManager.flashcards = notesProvider.flashcards.map((c) => c.toJson()).toList();
      voiceCommander.dialogueManager.currentCardIndex = notesProvider.flashcardIndex;

      if (notesProvider.flashcards.isNotEmpty) {
        if (!voiceCommander.isSpeaking) {
          _speakCurrentCard();
        }
      } else {
        if (!voiceCommander.isSpeaking) {
          voiceCommander.ttsService.speak(
            "No flashcards found. Say 'Make flashcards for Biology' or start a lecture session to capture notes.",
          );
        }
      }
    }
  }

  void _speakCurrentCard() {
    final notesProvider = context.read<NotesProvider>();
    final voiceCommander = context.read<VoiceCommander>();
    final card = notesProvider.currentFlashcard;
    if (card == null) return;

    final idx = notesProvider.flashcardIndex;
    final isFlipped = notesProvider.isCardFlipped;
    _lastSpokenIndex = idx;
    _lastSpokenFlipped = isFlipped;

    // Sync dialogueManager with active card
    voiceCommander.dialogueManager.currentMode = "flashcard_active";
    voiceCommander.dialogueManager.currentCardIndex = idx;

    final cardNum = idx + 1;
    final total = notesProvider.flashcards.length;

    if (isFlipped) {
      voiceCommander.ttsService.speak(
        "Answer for card $cardNum: ${card.back}. Rate difficulty: say Easy, Medium, or Hard, or say Next.",
      );
    } else {
      voiceCommander.ttsService.speak(
        "Card $cardNum of $total. Subject: ${card.subject}. Concept: ${card.front}. Say Flip to reveal the answer, or say Next.",
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesProvider = context.watch<NotesProvider>();
    final voiceCommander = context.watch<VoiceCommander>();

    final cards = notesProvider.flashcards;
    final currentIndex = notesProvider.flashcardIndex;
    final currentCard = notesProvider.currentFlashcard;
    final isFlipped = notesProvider.isCardFlipped;
    final isLoading = notesProvider.isLoadingFlashcards;

    // Keep dialogueManager in continuous sync
    if (cards.isNotEmpty) {
      voiceCommander.dialogueManager.currentMode = "flashcard_active";
      voiceCommander.dialogueManager.currentCardIndex = currentIndex;
      if (voiceCommander.dialogueManager.flashcards.length != cards.length) {
        voiceCommander.dialogueManager.flashcards = cards.map((c) => c.toJson()).toList();
      }
    }

    // Detect if external voice command changed the card index or flipped status
    if (currentCard != null && (currentIndex != _lastSpokenIndex || isFlipped != _lastSpokenFlipped)) {
      _lastSpokenIndex = currentIndex;
      _lastSpokenFlipped = isFlipped;
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Audio Flashcards",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22, color: AccessibleTheme.primaryGold),
        ),
        backgroundColor: AccessibleTheme.surface,
        actions: [
          IconButton(
            icon: const Icon(Icons.volume_up, color: AccessibleTheme.primaryGold, size: 28),
            tooltip: "Read card aloud",
            onPressed: currentCard != null ? () => _speakCurrentCard() : null,
          ),
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white, size: 28),
            tooltip: "Reload flashcards",
            onPressed: () async {
              await notesProvider.loadFlashcards();
              _speakCurrentCard();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Voice Indicator Header
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

            // Flashcard Session Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              color: AccessibleTheme.surfaceElevated,
              child: Row(
                children: [
                  const Icon(Icons.style, color: AccessibleTheme.primaryGold, size: 36),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          currentCard != null ? "SUBJECT: ${currentCard.subject.toUpperCase()}" : "FLASHCARD REVISION",
                          style: const TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 18),
                        ),
                        Text(
                          cards.isEmpty
                              ? "No active flashcards."
                              : "Card ${currentIndex + 1} of ${cards.length} • ${isFlipped ? "Answer Side (Back)" : "Question Side (Front)"}",
                          style: const TextStyle(color: Colors.white, fontSize: 16),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Active Card Container / Loading State
            Expanded(
              child: isLoading
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: const [
                          CircularProgressIndicator(color: AccessibleTheme.primaryGold, strokeWidth: 4),
                          SizedBox(height: 20),
                          Text(
                            "Generating audio flashcards from your notes...",
                            style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    )
                  : currentCard == null
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.style_outlined, size: 64, color: AccessibleTheme.primaryGold),
                                const SizedBox(height: 16),
                                const Text(
                                  "No flashcards loaded.",
                                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                                ),
                                const SizedBox(height: 8),
                                const Text(
                                  "Say \"Give me flashcards on Biology\" or \"Make flashcards from my notes\".",
                                  style: TextStyle(fontSize: 16, color: Colors.white70),
                                  textAlign: TextAlign.center,
                                ),
                                const SizedBox(height: 24),
                                AccessibleButton(
                                  label: "Load General Flashcards",
                                  icon: Icons.download,
                                  onPressed: () async {
                                    await notesProvider.loadFlashcards();
                                    _speakCurrentCard();
                                  },
                                ),
                              ],
                            ),
                          ),
                        )
                      : SingleChildScrollView(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Semantics(
                                container: true,
                                label: isFlipped
                                    ? "Flashcard ${currentIndex + 1} of ${cards.length}. Showing Back. Answer: ${currentCard.back}. Tap or say Flip to show question."
                                    : "Flashcard ${currentIndex + 1} of ${cards.length}. Showing Front. Question: ${currentCard.front}. Tap or say Flip to reveal answer.",
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(16),
                                  onTap: () {
                                    notesProvider.toggleCardFlip();
                                    _speakCurrentCard();
                                  },
                                  child: Card(
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(16),
                                      side: BorderSide(
                                        color: isFlipped ? AccessibleTheme.accentBlue : AccessibleTheme.primaryGold,
                                        width: 3.5,
                                      ),
                                    ),
                                    child: Padding(
                                      padding: const EdgeInsets.all(24),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                            children: [
                                              TagBadge(tag: currentCard.tag),
                                              Container(
                                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                                decoration: BoxDecoration(
                                                  color: isFlipped
                                                      ? Colors.blue.shade900.withOpacity(0.5)
                                                      : Colors.amber.shade900.withOpacity(0.4),
                                                  borderRadius: BorderRadius.circular(8),
                                                  border: Border.all(
                                                    color: isFlipped ? AccessibleTheme.accentBlue : AccessibleTheme.primaryGold,
                                                    width: 1.5,
                                                  ),
                                                ),
                                                child: Text(
                                                  isFlipped ? "BACK • ANSWER" : "FRONT • QUESTION",
                                                  style: TextStyle(
                                                    color: isFlipped ? AccessibleTheme.accentBlue : AccessibleTheme.primaryGold,
                                                    fontSize: 13,
                                                    fontWeight: FontWeight.bold,
                                                    letterSpacing: 0.5,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 20),
                                          if (!isFlipped) ...[
                                            const Text(
                                              "QUESTION / CONCEPT:",
                                              style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 15),
                                            ),
                                            const SizedBox(height: 10),
                                            Text(
                                              currentCard.front,
                                              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.white, height: 1.3),
                                            ),
                                            const SizedBox(height: 24),
                                            const Divider(color: Colors.white24, thickness: 1.5),
                                            const SizedBox(height: 12),
                                            Row(
                                              children: const [
                                                Icon(Icons.touch_app, color: Colors.white54, size: 18),
                                                SizedBox(width: 8),
                                                Text(
                                                  "Tap card or say \"Flip\" to reveal answer",
                                                  style: TextStyle(fontSize: 14, color: Colors.white60, fontStyle: FontStyle.italic),
                                                ),
                                              ],
                                            ),
                                          ] else ...[
                                            const Text(
                                              "GROUND TRUTH ANSWER:",
                                              style: TextStyle(color: AccessibleTheme.accentBlue, fontWeight: FontWeight.bold, fontSize: 15),
                                            ),
                                            const SizedBox(height: 10),
                                            Text(
                                              currentCard.back,
                                              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white, height: 1.3),
                                            ),
                                            const SizedBox(height: 20),
                                            const Divider(color: Colors.white24, thickness: 1.5),
                                            const SizedBox(height: 12),
                                            Text(
                                              "Question: ${currentCard.front}",
                                              style: const TextStyle(fontSize: 15, color: Colors.white60),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
            ),

            // Card Action Controls (Flip & Navigation)
            if (currentCard != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                color: AccessibleTheme.surfaceElevated,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    AccessibleButton(
                      label: "Previous",
                      icon: Icons.arrow_back,
                      isPrimary: false,
                      onPressed: currentIndex > 0
                          ? () {
                              notesProvider.previousFlashcard();
                              _speakCurrentCard();
                            }
                          : null,
                    ),
                    AccessibleButton(
                      label: isFlipped ? "Show Front" : "Flip Card",
                      icon: Icons.flip,
                      isPrimary: true,
                      onPressed: () {
                        notesProvider.toggleCardFlip();
                        _speakCurrentCard();
                      },
                    ),
                    AccessibleButton(
                      label: "Next",
                      icon: Icons.arrow_forward,
                      isPrimary: false,
                      onPressed: currentIndex + 1 < cards.length
                          ? () {
                              notesProvider.nextFlashcard();
                              _speakCurrentCard();
                            }
                          : null,
                    ),
                  ],
                ),
              ),

            // Spoken Flashcard Action Shortcuts
            Container(
              padding: const EdgeInsets.all(16),
              color: AccessibleTheme.surface,
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        "SAY OR TAP DIFFICULTY RATING",
                        style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                      TextButton.icon(
                        icon: const Icon(Icons.volume_up, color: AccessibleTheme.accentBlue, size: 18),
                        label: const Text("Repeat Card", style: TextStyle(color: AccessibleTheme.accentBlue, fontWeight: FontWeight.bold)),
                        onPressed: currentCard != null ? () => _speakCurrentCard() : null,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      AccessibleButton(
                        label: "Easy",
                        icon: Icons.sentiment_very_satisfied,
                        onPressed: () => voiceCommander.processUtterance("Easy."),
                      ),
                      AccessibleButton(
                        label: "Medium",
                        icon: Icons.sentiment_neutral,
                        isPrimary: false,
                        onPressed: () => voiceCommander.processUtterance("Medium."),
                      ),
                      AccessibleButton(
                        label: "Hard",
                        icon: Icons.sentiment_very_dissatisfied,
                        isPrimary: false,
                        onPressed: () => voiceCommander.processUtterance("Hard."),
                      ),
                      AccessibleButton(
                        label: "Explain",
                        icon: Icons.help_outline,
                        isPrimary: false,
                        onPressed: () => voiceCommander.processUtterance("Explain."),
                      ),
                    ],
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
