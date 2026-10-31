import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/theme.dart';
import '../core/services/voice_commander.dart';
import '../providers/notes_provider.dart';
import '../widgets/accessible_widgets.dart';

class AnalyticsScreen extends StatefulWidget {
  const AnalyticsScreen({super.key});

  @override
  State<AnalyticsScreen> createState() => _AnalyticsScreenState();
}

class _AnalyticsScreenState extends State<AnalyticsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final voiceCommander = context.read<VoiceCommander>();
      final notesProvider = context.read<NotesProvider>();
      voiceCommander.dialogueManager.currentMode = "analytics";
      
      notesProvider.loadAnalytics().then((_) {
        if (mounted && !voiceCommander.isSpeaking) {
          final summary = notesProvider.analyticsData["spoken_summary"] as String?;
          if (summary != null && summary.isNotEmpty) {
            voiceCommander.ttsService.speak(summary);
          } else {
            voiceCommander.ttsService.speak(
              "Study Analytics screen. Showing visual graphs of your notes across subjects, exam focus points, and knowledge concepts.",
            );
          }
        }
      });
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

  Color _getSubjectColor(String subject) {
    switch (subject.toLowerCase()) {
      case 'biology':
        return const Color(0xFF00E676);
      case 'geography':
        return const Color(0xFFFF9100);
      case 'computer science':
      case 'computerscience':
      case 'cs':
        return const Color(0xFF00E5FF);
      case 'chemistry':
        return const Color(0xFFBA68C8);
      case 'physics':
        return const Color(0xFFFF4081);
      case 'mathematics':
      case 'math':
        return const Color(0xFFFFD700);
      default:
        return const Color(0xFF64B5F6);
    }
  }

  IconData _getSubjectIcon(String subject) {
    switch (subject.toLowerCase()) {
      case 'biology':
        return Icons.eco;
      case 'geography':
        return Icons.public;
      case 'computer science':
      case 'computerscience':
      case 'cs':
        return Icons.computer;
      case 'chemistry':
        return Icons.science;
      case 'physics':
        return Icons.speed;
      case 'mathematics':
      case 'math':
        return Icons.calculate;
      default:
        return Icons.menu_book;
    }
  }

  @override
  Widget build(BuildContext context) {
    final notesProvider = context.watch<NotesProvider>();
    final voiceCommander = context.watch<VoiceCommander>();
    final analytics = notesProvider.analyticsData;

    final totalNotes = analytics["total_notes"] as int? ?? notesProvider.notes.length;
    final totalSessions = analytics["total_sessions"] as int? ?? 1;
    final subjectCounts = Map<String, dynamic>.from(analytics["subject_counts"] ?? {});
    final tagCounts = Map<String, dynamic>.from(analytics["tag_counts"] ?? {});
    final spokenSummary = analytics["spoken_summary"] as String? ?? 
        "You have $totalNotes total notes recorded across ${subjectCounts.length} subjects.";

    final importantCount = tagCounts["Important"] as int? ?? 0;
    final definitionCount = tagCounts["Definition"] as int? ?? 0;
    final exampleCount = tagCounts["Example"] as int? ?? 0;
    final generalCount = tagCounts["General"] as int? ?? 0;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: AccessibleTheme.surface,
        leading: Semantics(
          label: "Back to Home",
          button: true,
          child: IconButton(
            icon: const Icon(Icons.arrow_back, color: AccessibleTheme.primaryGold, size: 28),
            onPressed: () => Navigator.pop(context),
          ),
        ),
        title: Semantics(
          header: true,
          child: const Text(
            "Study Analytics & Graphs",
            style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 22),
          ),
        ),
        actions: [
          Semantics(
            label: voiceCommander.isSpeaking ? "Mute audio" : "Listen to complete summary",
            button: true,
            child: IconButton(
              icon: Icon(
                voiceCommander.isSpeaking ? Icons.volume_off : Icons.volume_up,
                color: AccessibleTheme.primaryGold,
                size: 28,
              ),
              onPressed: () {
                if (voiceCommander.isSpeaking) {
                  voiceCommander.interruptSpeech();
                } else {
                  voiceCommander.ttsService.speak(spokenSummary);
                }
              },
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: notesProvider.isLoadingAnalytics
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: AccessibleTheme.primaryGold, strokeWidth: 4),
                  SizedBox(height: 16),
                  Text("Aggregating study analytics...", style: TextStyle(color: Colors.white, fontSize: 18)),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Auditory Sonification Action Bar
                  Semantics(
                    container: true,
                    label: "Audio summary button. $spokenSummary",
                    child: Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AccessibleTheme.surfaceElevated,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AccessibleTheme.primaryGold, width: 2),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            voiceCommander.isSpeaking ? Icons.graphic_eq : Icons.campaign,
                            color: AccessibleTheme.primaryGold,
                            size: 36,
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  "Audio Sonification Report",
                                  style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 18),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  spokenSummary,
                                  maxLines: 3,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 10),
                          AccessibleButton(
                            label: voiceCommander.isSpeaking ? "Pause" : "Listen",
                            icon: voiceCommander.isSpeaking ? Icons.pause : Icons.play_arrow,
                            isPrimary: true,
                            onPressed: () {
                              if (voiceCommander.isSpeaking) {
                                voiceCommander.interruptSpeech();
                              } else {
                                voiceCommander.ttsService.speak(spokenSummary);
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),

                  // KPI Cards Grid
                  Semantics(
                    header: true,
                    child: const Text(
                      "OVERVIEW METRICS",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AccessibleTheme.primaryGold, letterSpacing: 1.2),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _buildMetricCard(
                          label: "Total Notes",
                          value: "$totalNotes",
                          icon: Icons.note_alt,
                          color: AccessibleTheme.primaryGold,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildMetricCard(
                          label: "Subjects",
                          value: "${subjectCounts.length}",
                          icon: Icons.school,
                          color: const Color(0xFF00E5FF),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: _buildMetricCard(
                          label: "Exam Points",
                          value: "$importantCount",
                          icon: Icons.star,
                          color: const Color(0xFFFF9100),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _buildMetricCard(
                          label: "Study Sessions",
                          value: "$totalSessions",
                          icon: Icons.history_edu,
                          color: const Color(0xFFBA68C8),
                        ),
                      ),
                    ],
                  ),

                  const SizedBox(height: 28),

                  // Visual Graph 1: Subject Distribution Bar Chart
                  Semantics(
                    header: true,
                    child: const Row(
                      children: [
                        Icon(Icons.bar_chart, color: AccessibleTheme.primaryGold, size: 24),
                        SizedBox(width: 8),
                        Text(
                          "SUBJECT DISTRIBUTION CHART",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AccessibleTheme.primaryGold, letterSpacing: 1.2),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AccessibleTheme.surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white24, width: 1.5),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (subjectCounts.isEmpty)
                          const Center(
                            child: Padding(
                              padding: EdgeInsets.all(24.0),
                              child: Text(
                                "No notes recorded yet. Start recording lecture notes to see subject visual charts.",
                                style: TextStyle(color: Colors.white70, fontSize: 16),
                                textAlign: TextAlign.center,
                              ),
                            ),
                          )
                        else
                          ...subjectCounts.entries.map((entry) {
                            final subject = entry.key;
                            final count = (entry.value as num).toInt();
                            final pct = totalNotes > 0 ? (count / totalNotes) : 0.0;
                            final pctString = (pct * 100).toStringAsFixed(1);
                            final color = _getSubjectColor(subject);
                            final icon = _getSubjectIcon(subject);

                            return Semantics(
                              container: true,
                              label: "$subject: $count notes, $pctString percent of all notes.",
                              child: Padding(
                                padding: const EdgeInsets.symmetric(vertical: 8),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(icon, color: color, size: 22),
                                        const SizedBox(width: 8),
                                        Text(
                                          subject,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 17, color: Colors.white),
                                        ),
                                        const Spacer(),
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                          decoration: BoxDecoration(
                                            color: color.withOpacity(0.2),
                                            borderRadius: BorderRadius.circular(8),
                                            border: Border.all(color: color, width: 1),
                                          ),
                                          child: Text(
                                            "$count notes ($pctString%)",
                                            style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14),
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    Stack(
                                      children: [
                                        Container(
                                          height: 18,
                                          decoration: BoxDecoration(
                                            color: Colors.white12,
                                            borderRadius: BorderRadius.circular(9),
                                          ),
                                        ),
                                        FractionallySizedBox(
                                          widthFactor: pct.clamp(0.02, 1.0),
                                          child: Container(
                                            height: 18,
                                            decoration: BoxDecoration(
                                              gradient: LinearGradient(
                                                colors: [color.withOpacity(0.7), color],
                                              ),
                                              borderRadius: BorderRadius.circular(9),
                                              border: Border.all(color: Colors.white, width: 1),
                                              boxShadow: [
                                                BoxShadow(
                                                  color: color.withOpacity(0.4),
                                                  blurRadius: 6,
                                                  offset: const Offset(0, 2),
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          }).toList(),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // Visual Graph 2: Tag & Exam Focus Distribution
                  Semantics(
                    header: true,
                    child: const Row(
                      children: [
                        Icon(Icons.pie_chart, color: AccessibleTheme.primaryGold, size: 24),
                        SizedBox(width: 8),
                        Text(
                          "NOTE CLASSIFICATION BREAKDOWN",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AccessibleTheme.primaryGold, letterSpacing: 1.2),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AccessibleTheme.surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white24, width: 1.5),
                    ),
                    child: Column(
                      children: [
                        _buildTagRow(
                          label: "Important (Exam Points)",
                          count: importantCount,
                          total: totalNotes,
                          color: AccessibleTheme.tagImportant,
                          icon: Icons.star,
                        ),
                        const Divider(color: Colors.white12, height: 24),
                        _buildTagRow(
                          label: "Definitions",
                          count: definitionCount,
                          total: totalNotes,
                          color: AccessibleTheme.tagDefinition,
                          icon: Icons.menu_book,
                        ),
                        const Divider(color: Colors.white12, height: 24),
                        _buildTagRow(
                          label: "Examples & Case Studies",
                          count: exampleCount,
                          total: totalNotes,
                          color: AccessibleTheme.tagExample,
                          icon: Icons.lightbulb,
                        ),
                        const Divider(color: Colors.white12, height: 24),
                        _buildTagRow(
                          label: "General Discussion",
                          count: generalCount,
                          total: totalNotes,
                          color: AccessibleTheme.tagGeneral,
                          icon: Icons.notes,
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 28),

                  // Visual Graph 3: Knowledge Concept Map
                  Semantics(
                    header: true,
                    child: const Row(
                      children: [
                        Icon(Icons.hub, color: AccessibleTheme.primaryGold, size: 24),
                        SizedBox(width: 8),
                        Text(
                          "KNOWLEDGE CONCEPT MAP",
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AccessibleTheme.primaryGold, letterSpacing: 1.2),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 14),

                  Container(
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      color: AccessibleTheme.surface,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white24, width: 1.5),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          "Connected Subject & Concept Nodes",
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          "Visual mapping between academic subjects and their key core concepts recorded in lectures.",
                          style: TextStyle(color: Colors.white70, fontSize: 14),
                        ),
                        const SizedBox(height: 16),

                        _buildConceptNode(
                          subject: "Biology",
                          concept: "Cell Division & Mitosis",
                          subConcept: "Prophase, Metaphase, Anaphase, Telophase",
                          status: "Mastered (High Volume)",
                          statusColor: const Color(0xFF00E676),
                          icon: Icons.eco,
                          onTap: () {
                            voiceCommander.ttsService.speak(
                              "Biology concept node: Cell Division and Mitosis. Prophase, Metaphase, Anaphase, Telophase. Mastered with high note volume.",
                            );
                          },
                        ),
                        const SizedBox(height: 12),
                        _buildConceptNode(
                          subject: "Geography",
                          concept: "Continental Drift & Earth Interior",
                          subConcept: "Plate Tectonics, Crust, Mantle, Core",
                          status: "Active Study",
                          statusColor: const Color(0xFFFF9100),
                          icon: Icons.public,
                          onTap: () {
                            voiceCommander.ttsService.speak(
                              "Geography concept node: Continental Drift and Earth Interior. Plate Tectonics, Crust, Mantle, and Core. Active study.",
                            );
                          },
                        ),
                        const SizedBox(height: 12),
                        _buildConceptNode(
                          subject: "Computer Science",
                          concept: "Algorithms & Logic",
                          subConcept: "Binary Search, Sorting, Computational Theory",
                          status: "In Progress",
                          statusColor: const Color(0xFF00E5FF),
                          icon: Icons.computer,
                          onTap: () {
                            voiceCommander.ttsService.speak(
                              "Computer Science concept node: Algorithms and Logic. Binary Search, Sorting, and Computational Theory. In progress.",
                            );
                          },
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Sighted / Voice Quick Actions
                  Semantics(
                    header: true,
                    child: const Text(
                      "STUDY ACTIONS",
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white70),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 12,
                    runSpacing: 12,
                    children: [
                      AccessibleButton(
                        label: "Open Recent Notes",
                        icon: Icons.history,
                        isPrimary: true,
                        onPressed: () => Navigator.pushNamed(context, '/recents'),
                      ),
                      AccessibleButton(
                        label: "Take Voice Quiz",
                        icon: Icons.quiz,
                        isPrimary: false,
                        onPressed: () => Navigator.pushNamed(context, '/quiz'),
                      ),
                      AccessibleButton(
                        label: "Audio Flashcards",
                        icon: Icons.style,
                        isPrimary: false,
                        onPressed: () => Navigator.pushNamed(context, '/flashcards'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 40),
                ],
              ),
            ),
    );
  }

  Widget _buildMetricCard({
    required String label,
    required String value,
    required IconData icon,
    required Color color,
  }) {
    return Semantics(
      container: true,
      label: "$label: $value",
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
        decoration: BoxDecoration(
          color: AccessibleTheme.surface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.6), width: 2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 26),
                const Spacer(),
                Text(
                  value,
                  style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 26),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              label,
              style: const TextStyle(color: Colors.white70, fontSize: 15, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTagRow({
    required String label,
    required int count,
    required int total,
    required Color color,
    required IconData icon,
  }) {
    final pct = total > 0 ? (count / total) : 0.0;
    final pctString = (pct * 100).toStringAsFixed(1);

    return Semantics(
      container: true,
      label: "$label: $count notes, $pctString percent",
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16),
                ),
              ),
              Text(
                "$count notes ($pctString%)",
                style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 14),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Stack(
            children: [
              Container(
                height: 12,
                decoration: BoxDecoration(
                  color: Colors.white12,
                  borderRadius: BorderRadius.circular(6),
                ),
              ),
              FractionallySizedBox(
                widthFactor: pct.clamp(0.02, 1.0),
                child: Container(
                  height: 12,
                  decoration: BoxDecoration(
                    color: color,
                    borderRadius: BorderRadius.circular(6),
                    boxShadow: [
                      BoxShadow(color: color.withOpacity(0.4), blurRadius: 4, offset: const Offset(0, 1)),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildConceptNode({
    required String subject,
    required String concept,
    required String subConcept,
    required String status,
    required Color statusColor,
    required IconData icon,
    required VoidCallback onTap,
  }) {
    return Semantics(
      container: true,
      button: true,
      label: "$subject concept node: $concept. Sub-topics: $subConcept. Status: $status.",
      child: Material(
        color: AccessibleTheme.surfaceElevated,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: statusColor.withOpacity(0.6), width: 1.5),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.15),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, color: statusColor, size: 24),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            subject,
                            style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 0.5),
                          ),
                          const SizedBox(width: 8),
                          const Icon(Icons.arrow_forward, size: 14, color: Colors.white54),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              concept,
                              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subConcept,
                        style: const TextStyle(color: Colors.white70, fontSize: 13),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: statusColor, width: 1),
                  ),
                  child: Text(
                    status,
                    style: TextStyle(color: statusColor, fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
