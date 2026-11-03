import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants/theme.dart';
import '../core/services/voice_commander.dart';
import '../providers/settings_provider.dart';
import '../widgets/accessible_widgets.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlController;
  late TextEditingController _geminiKeyController;
  bool _isBackendConnected = false;
  bool _isChecking = false;
  bool _isGeminiAvailable = false;
  bool _hasGeminiKey = false;
  String _geminiKeyPreview = "";
  String _geminiModel = "";
  bool _isSavingGemini = false;
  String? _geminiStatusMessage;

  @override
  void initState() {
    super.initState();
    final settings = context.read<SettingsProvider>();
    _urlController = TextEditingController(text: settings.backendUrl);
    _geminiKeyController = TextEditingController();
    _checkHealth();
    _loadGeminiSettings();
  }

  Future<void> _checkHealth() async {
    setState(() => _isChecking = true);
    final voiceCommander = context.read<VoiceCommander>();
    final connected = await voiceCommander.apiClient.checkHealth();
    setState(() {
      _isBackendConnected = connected;
      _isChecking = false;
    });
  }

  Future<void> _loadGeminiSettings() async {
    final voiceCommander = context.read<VoiceCommander>();
    final data = await voiceCommander.apiClient.getGeminiSettings();
    if (data != null && mounted) {
      setState(() {
        _isGeminiAvailable = data["gemini_available"] == true;
        _hasGeminiKey = data["has_key"] == true;
        _geminiKeyPreview = data["key_preview"] ?? "";
        _geminiModel = data["model"] ?? "";
      });
    }
  }

  Future<void> _saveGeminiKey() async {
    final key = _geminiKeyController.text.trim();
    if (key.isEmpty) return;
    setState(() => _isSavingGemini = true);
    final voiceCommander = context.read<VoiceCommander>();
    final res = await voiceCommander.apiClient.updateGeminiKey(key);
    if (mounted) {
      setState(() {
        _isSavingGemini = false;
        if (res != null) {
          _isGeminiAvailable = res["gemini_available"] == true;
          _hasGeminiKey = res["success"] == true;
          _geminiStatusMessage = res["message"];
        }
      });
      _geminiKeyController.clear();
      await _loadGeminiSettings();
      if (_isGeminiAvailable) {
        voiceCommander.ttsService.speak("Google Gemini AI connected successfully.");
      } else {
        voiceCommander.ttsService.speak("Gemini key saved, running in multi-subject curriculum mode.");
      }
    }
  }

  @override
  void dispose() {
    _urlController.dispose();
    _geminiKeyController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsProvider>();
    final voiceCommander = context.watch<VoiceCommander>();

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          "Accessible Settings",
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22, color: AccessibleTheme.primaryGold),
        ),
        backgroundColor: AccessibleTheme.surface,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            // Backend Connection Status Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "BACKEND CONNECTION",
                      style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Icon(
                          _isBackendConnected ? Icons.check_circle : Icons.error,
                          color: _isBackendConnected ? AccessibleTheme.successGreen : AccessibleTheme.errorRed,
                          size: 28,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _isBackendConnected
                                ? "Backend Connected (${Uri.tryParse(settings.backendUrl)?.host ?? settings.backendUrl})"
                                : "Backend Disconnected",
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                        ),
                        _isChecking
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(strokeWidth: 2, color: AccessibleTheme.primaryGold),
                              )
                            : IconButton(
                                icon: const Icon(Icons.refresh, color: Colors.white),
                                onPressed: _checkHealth,
                                tooltip: "Check Connection",
                              ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: _urlController,
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                      decoration: const InputDecoration(
                        labelText: "Backend API URL",
                        labelStyle: TextStyle(color: AccessibleTheme.primaryGold),
                        border: OutlineInputBorder(),
                        focusedBorder: OutlineInputBorder(borderSide: BorderSide(color: AccessibleTheme.primaryGold, width: 2)),
                      ),
                      onSubmitted: (val) {
                        settings.updateBackendUrl(val);
                        voiceCommander.apiClient.baseUrl = val;
                        _checkHealth();
                      },
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Google Gemini AI Intelligence Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Expanded(
                          child: Text(
                            "GEMINI AI & KNOWLEDGE",
                            style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: _isGeminiAvailable ? AccessibleTheme.successGreen.withOpacity(0.2) : Colors.amber.withOpacity(0.2),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: _isGeminiAvailable ? AccessibleTheme.successGreen : Colors.amber,
                            ),
                          ),
                          child: Text(
                            _isGeminiAvailable ? "ONLINE AI ACTIVE" : "OFFLINE CURRICULUM",
                            style: TextStyle(
                              color: _isGeminiAvailable ? AccessibleTheme.successGreen : Colors.amber,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _isGeminiAvailable
                          ? "Google Gemini AI model (${_geminiModel.isEmpty ? 'gemini-2.5-flash' : _geminiModel}) is active for acoustic speech auto-correction, dynamic quizzes, and note generation."
                          : "Offline multi-subject curriculum active covering Chemistry, Physics, Computer Science, Mathematics, History, and Biology with high-yield notes and flashcards.",
                      style: const TextStyle(color: Colors.white, fontSize: 14, height: 1.4),
                    ),
                    if (_hasGeminiKey) ...[
                      const SizedBox(height: 8),
                      Text(
                        "Configured Key: $_geminiKeyPreview",
                        style: const TextStyle(color: AccessibleTheme.accentBlue, fontSize: 13, fontFamily: "monospace"),
                      ),
                    ],
                    const SizedBox(height: 14),
                    TextField(
                      controller: _geminiKeyController,
                      obscureText: true,
                      style: const TextStyle(color: Colors.white, fontSize: 16),
                      decoration: InputDecoration(
                        labelText: _hasGeminiKey ? "Update Gemini API Key" : "Enter Google Gemini API Key",
                        labelStyle: const TextStyle(color: AccessibleTheme.primaryGold),
                        hintText: "AIzaSy...",
                        hintStyle: const TextStyle(color: Colors.white38),
                        border: const OutlineInputBorder(),
                        focusedBorder: const OutlineInputBorder(
                          borderSide: BorderSide(color: AccessibleTheme.primaryGold, width: 2),
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    if (_geminiStatusMessage != null) ...[
                      Text(
                        _geminiStatusMessage!,
                        style: TextStyle(
                          color: _isGeminiAvailable ? AccessibleTheme.successGreen : Colors.amber,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 8),
                    ],
                    AccessibleButton(
                      label: _isSavingGemini ? "Connecting..." : (_hasGeminiKey ? "Update API Key" : "Save & Connect Gemini"),
                      icon: Icons.auto_awesome,
                      onPressed: _isSavingGemini ? null : _saveGeminiKey,
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Voice & Speech Output Settings Card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "SPEECH SYNTHESIS (TTS)",
                      style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 16),
                    
                    // Speech Rate Slider
                    Text(
                      "Speech Rate: ${(settings.speechRate * 2).toStringAsFixed(1)}x",
                      style: const TextStyle(fontSize: 18, color: Colors.white),
                    ),
                    Slider(
                      value: settings.speechRate,
                      min: 0.2,
                      max: 1.0,
                      divisions: 8,
                      activeColor: AccessibleTheme.primaryGold,
                      inactiveColor: Colors.white24,
                      onChanged: (val) {
                        settings.updateSpeechRate(val);
                        voiceCommander.ttsService.setRate(val);
                      },
                    ),

                    const SizedBox(height: 12),

                    // Speech Pitch Slider
                    Text(
                      "Speech Pitch: ${settings.speechPitch.toStringAsFixed(1)}",
                      style: const TextStyle(fontSize: 18, color: Colors.white),
                    ),
                    Slider(
                      value: settings.speechPitch,
                      min: 0.5,
                      max: 1.5,
                      divisions: 10,
                      activeColor: AccessibleTheme.accentBlue,
                      inactiveColor: Colors.white24,
                      onChanged: (val) {
                        settings.updateSpeechPitch(val);
                        voiceCommander.ttsService.setPitch(val);
                      },
                    ),

                    const SizedBox(height: 12),

                    // Test Voice Output Button
                    AccessibleButton(
                      label: "Test Voice Feedback",
                      icon: Icons.volume_up,
                      onPressed: () {
                        voiceCommander.ttsService.speak("Voice-First test. Speech rate and pitch configured successfully.");
                      },
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Voice Interaction Settings
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "VOICE PREFERENCES",
                      style: TextStyle(color: AccessibleTheme.primaryGold, fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    const SizedBox(height: 12),
                    SwitchListTile(
                      title: const Text("Continuous Auto-Listening", style: TextStyle(color: Colors.white, fontSize: 16)),
                      subtitle: const Text("Automatically resumes listening after speaking answers", style: TextStyle(color: Colors.white70)),
                      value: settings.autoListen,
                      activeColor: AccessibleTheme.primaryGold,
                      onChanged: (val) {
                        settings.toggleAutoListen(val);
                        voiceCommander.setAutoListen(val);
                      },
                    ),
                    SwitchListTile(
                      title: const Text("Spoken Confirmations", style: TextStyle(color: Colors.white, fontSize: 16)),
                      subtitle: const Text("Announce confirmations after every note capture and tag", style: TextStyle(color: Colors.white70)),
                      value: settings.spokenConfirmation,
                      activeColor: AccessibleTheme.primaryGold,
                      onChanged: (val) {
                        settings.toggleSpokenConfirmation(val);
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
