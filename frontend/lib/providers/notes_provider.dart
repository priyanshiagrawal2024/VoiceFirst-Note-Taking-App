import 'package:flutter/foundation.dart';
import '../core/models/note_model.dart';
import '../core/models/session_model.dart';
import '../core/models/flashcard_model.dart';
import '../core/network/api_client.dart';

class NotesProvider extends ChangeNotifier {
  final ApiClient apiClient;

  List<NoteModel> _notes = [];
  NoteModel? _lastNote;
  SessionModel? _activeSession;
  
  List<NoteModel> _searchResults = [];
  String _searchQuery = "";
  int _searchIndex = 0;

  List<NoteModel> _reviewNotes = [];
  int _reviewIndex = 0;

  List<FlashcardModel> _flashcards = [];
  int _flashcardIndex = 0;
  bool _isCardFlipped = false;

  List<QuizQuestionModel> _quizItems = [];
  int _quizIndex = 0;
  double _quizScore = 0.0;
  QuizEvaluationModel? _lastQuizEvaluation;

  List<Map<String, dynamic>> _bookmarks = [];
  List<Map<String, dynamic>> _weakTopics = [];

  Map<String, dynamic> _analyticsData = {};
  Map<String, dynamic> get analyticsData => _analyticsData;
  bool _isLoadingAnalytics = false;
  bool get isLoadingAnalytics => _isLoadingAnalytics;

  String _selectedSubject = "All";
  String get selectedSubject => _selectedSubject;

  String? _currentlyPlayingNoteId;
  String? get currentlyPlayingNoteId => _currentlyPlayingNoteId;

  List<NoteModel> get notes => _notes;
  NoteModel? get lastNote => _lastNote;
  SessionModel? get activeSession => _activeSession;
  bool get hasActiveLecture => _activeSession != null && _activeSession!.isActive;

  void setSubjectFilter(String subject) {
    _selectedSubject = subject;
    notifyListeners();
  }

  void setCurrentlyPlayingNoteId(String? noteId) {
    _currentlyPlayingNoteId = noteId;
    notifyListeners();
  }

  bool isNotePlaying(NoteModel note) => _currentlyPlayingNoteId == note.noteId;

  List<String> get availableSubjects {
    final subjects = <String>{"All"};
    for (final note in _notes) {
      if (note.subject.trim().isNotEmpty) {
        final s = note.subject.trim();
        subjects.add(s[0].toUpperCase() + s.substring(1));
      }
    }
    const standardSubjects = ["Biology", "Geography", "Chemistry", "Physics", "Computer Science", "Mathematics", "History"];
    for (final s in standardSubjects) {
      subjects.add(s);
    }
    return subjects.toList();
  }

  List<NoteModel> get recentNotes {
    final list = List<NoteModel>.from(_notes);
    list.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return list;
  }

  List<NoteModel> get filteredRecentNotes {
    if (_selectedSubject == "All") {
      return recentNotes;
    }
    return recentNotes.where((n) => n.subject.toLowerCase() == _selectedSubject.toLowerCase()).toList();
  }

  List<NoteModel> get searchResults => _searchResults;
  String get searchQuery => _searchQuery;
  int get searchIndex => _searchIndex;
  NoteModel? get currentSearchNote => (_searchResults.isNotEmpty && _searchIndex < _searchResults.length) ? _searchResults[_searchIndex] : null;

  List<NoteModel> get reviewNotes => _reviewNotes;
  int get reviewIndex => _reviewIndex;
  NoteModel? get currentReviewNote => (_reviewNotes.isNotEmpty && _reviewIndex < _reviewNotes.length) ? _reviewNotes[_reviewIndex] : null;

  List<FlashcardModel> get flashcards => _flashcards;
  int get flashcardIndex => _flashcardIndex;
  bool get isCardFlipped => _isCardFlipped;
  FlashcardModel? get currentFlashcard => (_flashcards.isNotEmpty && _flashcardIndex < _flashcards.length) ? _flashcards[_flashcardIndex] : null;

  List<QuizQuestionModel> get quizItems => _quizItems;
  int get quizIndex => _quizIndex;
  double get quizScore => _quizScore;
  QuizEvaluationModel? get lastQuizEvaluation => _lastQuizEvaluation;
  QuizQuestionModel? get currentQuizItem => (_quizItems.isNotEmpty && _quizIndex < _quizItems.length) ? _quizItems[_quizIndex] : null;

  List<Map<String, dynamic>> get bookmarks => _bookmarks;
  List<Map<String, dynamic>> get weakTopics => _weakTopics;

  NotesProvider({required this.apiClient});

  Future<void> fetchNotes({String? subject, String? tag, String? timeframe}) async {
    _notes = await apiClient.getNotes(subject: subject, tag: tag, timeframe: timeframe);
    notifyListeners();
  }

  Future<void> fetchActiveSession() async {
    _activeSession = await apiClient.getActiveSession();
    notifyListeners();
  }

  Future<void> fetchLastNote() async {
    _lastNote = await apiClient.getLastNote();
    notifyListeners();
  }

  Future<void> fetchBookmarks() async {
    _bookmarks = await apiClient.getBookmarks();
    notifyListeners();
  }

  Future<bool> deleteNote(String noteId) async {
    final success = await apiClient.deleteNote(noteId);
    _notes.removeWhere((n) => n.noteId == noteId);
    _reviewNotes.removeWhere((n) => n.noteId == noteId);
    _searchResults.removeWhere((n) => n.noteId == noteId);
    if (_lastNote?.noteId == noteId) {
      _lastNote = _notes.isNotEmpty ? _notes.first : null;
    }
    if (_currentlyPlayingNoteId == noteId) {
      _currentlyPlayingNoteId = null;
    }
    notifyListeners();
    return success;
  }

  bool _isSearching = false;
  bool get isSearching => _isSearching;

  Future<void> performSearch(String query) async {
    _isSearching = true;
    _searchQuery = query;
    notifyListeners();
    try {
      final results = await apiClient.searchNotes(query);
      _searchResults = results;
      _searchIndex = 0;
    } catch (e) {
      debugPrint('[NotesProvider] performSearch error: $e');
    } finally {
      _isSearching = false;
      notifyListeners();
    }
  }

  void setSearchIndex(int index) {
    if (index >= 0 && index < _searchResults.length) {
      _searchIndex = index;
      notifyListeners();
    }
  }

  bool _isLoadingFlashcards = false;
  bool _isLoadingQuiz = false;

  bool get isLoadingFlashcards => _isLoadingFlashcards;
  bool get isLoadingQuiz => _isLoadingQuiz;

  void toggleCardFlip() {
    _isCardFlipped = !_isCardFlipped;
    notifyListeners();
  }

  void nextFlashcard() {
    if (_flashcardIndex + 1 < _flashcards.length) {
      _flashcardIndex++;
      _isCardFlipped = false;
      notifyListeners();
    }
  }

  void previousFlashcard() {
    if (_flashcardIndex > 0) {
      _flashcardIndex--;
      _isCardFlipped = false;
      notifyListeners();
    }
  }

  Future<void> loadFlashcards({String? topic}) async {
    _isLoadingFlashcards = true;
    notifyListeners();
    try {
      final cards = await apiClient.generateFlashcards(topic: topic);
      if (cards.isNotEmpty) {
        _flashcards = cards;
        _flashcardIndex = 0;
        _isCardFlipped = false;
      }
    } catch (e) {
      debugPrint("[NotesProvider] Error loading flashcards: $e");
    } finally {
      _isLoadingFlashcards = false;
      notifyListeners();
    }
  }

  Future<void> loadQuiz({String? topic}) async {
    _isLoadingQuiz = true;
    notifyListeners();
    try {
      final questions = await apiClient.generateQuiz(topic: topic);
      if (questions.isNotEmpty) {
        _quizItems = questions;
        _quizIndex = 0;
        _quizScore = 0.0;
        _lastQuizEvaluation = null;
      }
    } catch (e) {
      debugPrint("[NotesProvider] Error loading quiz: $e");
    } finally {
      _isLoadingQuiz = false;
      notifyListeners();
    }
  }

  void selectQuizOption(String optionLetter) {
    if (currentQuizItem != null) {
      final cleanLetter = optionLetter.trim().toUpperCase();
      currentQuizItem!.selectedOption = cleanLetter;
      if (cleanLetter == currentQuizItem!.correctAnswer) {
        _quizScore += 1.0;
      }
      notifyListeners();
    }
  }

  void nextQuizQuestion() {
    if (_quizIndex + 1 < _quizItems.length) {
      _quizIndex++;
      notifyListeners();
    }
  }

  void previousQuizQuestion() {
    if (_quizIndex > 0) {
      _quizIndex--;
      notifyListeners();
    }
  }

  Future<void> loadAnalytics() async {
    _isLoadingAnalytics = true;
    notifyListeners();
    try {
      final data = await apiClient.getAnalytics();
      if (data.isNotEmpty) {
        _analyticsData = data;
      }
    } catch (e) {
      debugPrint("[NotesProvider] Error loading analytics: $e");
    } finally {
      _isLoadingAnalytics = false;
      notifyListeners();
    }
  }

  void handleAction(String action, Map<String, dynamic> data) {
    switch (action) {
      case "NAVIGATE_ACTIVE_LECTURE":
        if (data.containsKey("session")) {
          _activeSession = SessionModel.fromJson(data["session"]);
        }
        break;

      case "NAVIGATE_HOME":
        _activeSession = null;
        break;

      case "NOTE_CREATED":
        if (data.containsKey("note")) {
          final newNote = NoteModel.fromJson(data["note"]);
          _notes.insert(0, newNote);
          _lastNote = newNote;
        }
        break;

      case "NOTE_UPDATED":
      case "NOTE_CORRECTED":
        if (data.containsKey("note")) {
          final updated = NoteModel.fromJson(data["note"]);
          _lastNote = updated;
          final idx = _notes.indexWhere((n) => n.noteId == updated.noteId);
          if (idx != -1) {
            _notes[idx] = updated;
          } else {
            _notes.insert(0, updated);
          }
        }
        break;

      case "NOTE_DELETED":
        final delId = data["note_id"];
        if (delId != null) {
          _notes.removeWhere((n) => n.noteId == delId);
          _reviewNotes.removeWhere((n) => n.noteId == delId);
          _searchResults.removeWhere((n) => n.noteId == delId);
          if (_lastNote?.noteId == delId) {
            _lastNote = _notes.isNotEmpty ? _notes.first : null;
          }
          if (_currentlyPlayingNoteId == delId) {
            _currentlyPlayingNoteId = null;
          }
        }
        break;

      case "NAVIGATE_RETRIEVAL":
        if (data.containsKey("results")) {
          final List list = data["results"];
          _searchResults = list.map((item) => NoteModel.fromJson(item)).toList();
          _searchQuery = data["query"] ?? "";
          _searchIndex = data["current_index"] ?? 0;
        }
        break;

      case "NAVIGATE_AUDIO_REVIEW":
        if (data.containsKey("notes")) {
          final List list = data["notes"];
          _reviewNotes = list.map((item) => NoteModel.fromJson(item)).toList();
          _reviewIndex = data["current_index"] ?? 0;
        }
        if (data.containsKey("subject_filter")) {
          _selectedSubject = data["subject_filter"] ?? "All";
        }
        break;

      case "NAVIGATE_RECENTS":
        if (data.containsKey("notes")) {
          final List list = data["notes"];
          _notes = list.map((item) => NoteModel.fromJson(item)).toList();
        }
        _selectedSubject = "All";
        break;

      case "NAVIGATE_ANALYTICS":
        if (data.containsKey("analytics")) {
          _analyticsData = Map<String, dynamic>.from(data["analytics"]);
        }
        break;

      case "AUDIO_INDEX_UPDATED":
        if (data.containsKey("current_index")) {
          _searchIndex = data["current_index"];
          _reviewIndex = data["current_index"];
        }
        break;

      case "AUDIO_NEXT":
        if (_flashcards.isNotEmpty && _flashcardIndex + 1 < _flashcards.length) {
          _flashcardIndex++;
          _isCardFlipped = false;
        }
        break;

      case "NAVIGATE_FLASHCARDS":
        final rawCards = data["flashcards"] ?? data["cards"];
        if (rawCards != null && rawCards is List) {
          _flashcards = rawCards.map((item) => FlashcardModel.fromJson(Map<String, dynamic>.from(item))).toList();
          _flashcardIndex = data["current_index"] ?? 0;
          _isCardFlipped = false;
        }
        break;

      case "FLASHCARD_FLIP":
        _isCardFlipped = data["is_flipped"] ?? !_isCardFlipped;
        break;

      case "FLASHCARD_INDEX_UPDATED":
        if (data.containsKey("current_index")) {
          _flashcardIndex = data["current_index"];
        }
        _isCardFlipped = data["is_flipped"] ?? false;
        break;

      case "FLASHCARD_SKIP":
        if (_flashcardIndex + 1 < _flashcards.length) {
          _flashcardIndex++;
          _isCardFlipped = false;
        }
        break;

      case "FLASHCARDS_COMPLETED":
        _isCardFlipped = false;
        break;

      case "NAVIGATE_QUIZ":
        final rawQuiz = data["questions"] ?? data["quiz_items"];
        if (rawQuiz != null && rawQuiz is List) {
          _quizItems = rawQuiz.map((item) => QuizQuestionModel.fromJson(Map<String, dynamic>.from(item))).toList();
          _quizIndex = data["current_index"] ?? 0;
          _quizScore = 0.0;
        }
        break;

      case "QUIZ_INDEX_UPDATED":
        if (data.containsKey("current_index")) {
          _quizIndex = data["current_index"];
        }
        break;

      case "QUIZ_ANSWER_EVALUATED":
        if (data.containsKey("next_index")) {
          _quizIndex = data["next_index"];
        }
        if (data.containsKey("score")) {
          _quizScore = (data["score"] as num).toDouble();
        }
        if (data.containsKey("evaluation") && data["evaluation"] != null) {
          _lastQuizEvaluation = QuizEvaluationModel.fromJson(Map<String, dynamic>.from(data["evaluation"]));
        }
        if (data.containsKey("selected_option") && currentQuizItem != null) {
          currentQuizItem!.selectedOption = data["selected_option"];
        }
        break;

      case "QUIZ_COMPLETED":
        if (data.containsKey("final_score")) {
          _quizScore = (data["final_score"] as num).toDouble();
        }
        if (data.containsKey("evaluation") && data["evaluation"] != null) {
          _lastQuizEvaluation = QuizEvaluationModel.fromJson(Map<String, dynamic>.from(data["evaluation"]));
        }
        break;
    }
    notifyListeners();
  }
}
