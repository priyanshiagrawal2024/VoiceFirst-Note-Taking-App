import 'package:flutter_test/flutter_test.dart';
import '../lib/core/models/flashcard_model.dart';
import '../lib/core/network/api_client.dart';
import '../lib/providers/notes_provider.dart';

void main() {
  group('QuizQuestionModel Tests', () {
    test('QuizQuestionModel fromJson and toJson roundtrip', () {
      final json = {
        'question_id': 'q_101',
        'source_note_id': 'note_12',
        'subject': 'Biology',
        'tag': 'Definition',
        'question': 'What is the primary function of Mitochondria?',
        'options': ['Energy generation', 'Protein synthesis', 'Cell wall formation', 'DNA storage'],
        'correct_answer': 'A',
        'expected_answer': 'Mitochondria produces ATP for the cell.',
        'original_note': 'Mitochondria is the powerhouse of the cell.',
      };

      final q = QuizQuestionModel.fromJson(json);
      expect(q.questionId, equals('q_101'));
      expect(q.subject, equals('Biology'));
      expect(q.options.length, equals(4));
      expect(q.correctAnswer, equals('A'));

      final serialized = q.toJson();
      expect(serialized['question_id'], equals('q_101'));
      expect(serialized['correct_answer'], equals('A'));
    });

    test('QuizEvaluationModel fromJson parses score and feedback', () {
      final json = {
        'result': 'Correct',
        'score': 1.0,
        'feedback': 'Great job!',
        'spoken_feedback': 'Correct! Option A is right.',
      };

      final eval = QuizEvaluationModel.fromJson(json);
      expect(eval.result, equals('Correct'));
      expect(eval.score, equals(1.0));
      expect(eval.spokenFeedback, contains('Option A'));
    });
  });

  group('NotesProvider Flashcards & Quiz Action Tests', () {
    late NotesProvider provider;

    setUp(() {
      provider = NotesProvider(apiClient: ApiClient());
    });

    test('handleAction NAVIGATE_FLASHCARDS populates cards and resets flip', () {
      provider.handleAction('NAVIGATE_FLASHCARDS', {
        'flashcards': [
          {
            'id': 'fc_1',
            'front': 'What is photosynthesis?',
            'back': 'The process of turning sunlight into glucose.',
            'subject': 'Biology',
            'tag': 'Definition',
          },
          {
            'id': 'fc_2',
            'front': 'What is cellular respiration?',
            'back': 'Breaking down glucose to release ATP.',
            'subject': 'Biology',
            'tag': 'Concept',
          }
        ],
        'current_index': 0,
      });

      expect(provider.flashcards.length, equals(2));
      expect(provider.flashcardIndex, equals(0));
      expect(provider.isCardFlipped, isFalse);
      expect(provider.currentFlashcard?.front, contains('photosynthesis'));
    });

    test('toggleCardFlip toggles front and back', () {
      expect(provider.isCardFlipped, isFalse);
      provider.toggleCardFlip();
      expect(provider.isCardFlipped, isTrue);
      provider.toggleCardFlip();
      expect(provider.isCardFlipped, isFalse);
    });

    test('handleAction FLASHCARD_FLIP updates flipped state', () {
      provider.handleAction('FLASHCARD_FLIP', {'is_flipped': true});
      expect(provider.isCardFlipped, isTrue);
    });

    test('handleAction NAVIGATE_QUIZ and QUIZ_ANSWER_EVALUATED update quiz state', () {
      provider.handleAction('NAVIGATE_QUIZ', {
        'questions': [
          {
            'question_id': 'q_1',
            'question': 'What does DNA stand for?',
            'options': ['Deoxyribonucleic acid', 'Ribonucleic acid'],
            'correct_answer': 'A',
            'expected_answer': 'Deoxyribonucleic acid',
          },
          {
            'question_id': 'q_2',
            'question': 'What is Mitosis?',
            'options': ['Cell division', 'Cell destruction'],
            'correct_answer': 'A',
            'expected_answer': 'Cell division',
          }
        ],
        'current_index': 0,
      });

      expect(provider.quizItems.length, equals(2));
      expect(provider.quizIndex, equals(0));
      expect(provider.currentQuizItem?.question, contains('DNA'));

      // Simulate backend action for evaluated answer
      provider.handleAction('QUIZ_ANSWER_EVALUATED', {
        'selected_option': 'A',
        'score': 1.0,
        'next_index': 1,
        'evaluation': {
          'result': 'Correct',
          'score': 1.0,
          'spoken_feedback': 'Option A is correct!',
        }
      });

      expect(provider.quizIndex, equals(1));
      expect(provider.quizScore, equals(1.0));
      expect(provider.lastQuizEvaluation?.result, equals('Correct'));
    });

    test('selectQuizOption increments score for correct answers', () {
      provider.handleAction('NAVIGATE_QUIZ', {
        'questions': [
          {
            'question_id': 'q_1',
            'question': 'What is binary 10?',
            'options': ['Two', 'Three'],
            'correct_answer': 'A',
            'expected_answer': 'Two',
          }
        ],
        'current_index': 0,
      });

      expect(provider.quizScore, equals(0.0));
      provider.selectQuizOption('A');
      expect(provider.quizScore, equals(1.0));
      expect(provider.currentQuizItem?.selectedOption, equals('A'));
    });

    test('handleAction FLASHCARD_INDEX_UPDATED and FLASHCARD_SKIP advance card index', () {
      provider.handleAction('NAVIGATE_FLASHCARDS', {
        'flashcards': [
          {'id': 'fc_1', 'front': 'Q1', 'back': 'A1', 'subject': 'Physics'},
          {'id': 'fc_2', 'front': 'Q2', 'back': 'A2', 'subject': 'Physics'},
        ],
        'current_index': 0,
      });

      expect(provider.flashcardIndex, equals(0));
      provider.handleAction('FLASHCARD_SKIP', {});
      expect(provider.flashcardIndex, equals(1));
      expect(provider.isCardFlipped, isFalse);

      provider.handleAction('FLASHCARD_FLIP', {'is_flipped': true});
      expect(provider.isCardFlipped, isTrue);

      provider.handleAction('FLASHCARD_INDEX_UPDATED', {'current_index': 0, 'is_flipped': false});
      expect(provider.flashcardIndex, equals(0));
      expect(provider.isCardFlipped, isFalse);
    });

    test('Subject filter and recent notes functionality', () {
      provider.handleAction('NOTE_CREATED', {
        'note': {
          'note_id': 'n_1',
          'user_id': 'u1',
          'subject': 'Chemistry',
          'text': 'Boyle law relates pressure and volume.',
          'tag': 'Definition',
          'timestamp': '10:00 AM',
          'created_at': '2026-10-25T10:00:00',
          'updated_at': '2026-10-25T10:00:00',
        }
      });
      provider.handleAction('NOTE_CREATED', {
        'note': {
          'note_id': 'n_2',
          'user_id': 'u1',
          'subject': 'Biology',
          'text': 'Mitosis is division.',
          'tag': 'Definition',
          'timestamp': '10:05 AM',
          'created_at': '2026-10-25T10:05:00',
          'updated_at': '2026-10-25T10:05:00',
        }
      });

      expect(provider.recentNotes.length, equals(2));
      expect(provider.availableSubjects, contains('Chemistry'));
      expect(provider.availableSubjects, contains('Biology'));

      provider.setSubjectFilter('Chemistry');
      expect(provider.filteredRecentNotes.length, equals(1));
      expect(provider.filteredRecentNotes.first.subject, equals('Chemistry'));

      provider.setSubjectFilter('All');
      expect(provider.filteredRecentNotes.length, equals(2));
    });

    test('deleteNote and handleAction NOTE_DELETED removes note from lists', () {
      provider.handleAction('NOTE_CREATED', {
        'note': {
          'note_id': 'del_1',
          'user_id': 'u1',
          'subject': 'Physics',
          'text': 'Incorrectly recorded note to delete.',
          'tag': 'General',
          'timestamp': '11:00 AM',
          'created_at': '2026-10-25T11:00:00',
          'updated_at': '2026-10-25T11:00:00',
        }
      });
      expect(provider.notes.any((n) => n.noteId == 'del_1'), isTrue);

      // Delete via action
      provider.handleAction('NOTE_DELETED', {'note_id': 'del_1'});
      expect(provider.notes.any((n) => n.noteId == 'del_1'), isFalse);
      expect(provider.filteredRecentNotes.any((n) => n.noteId == 'del_1'), isFalse);
    });

    test('handleAction NAVIGATE_RETRIEVAL and searchIndex selection', () {
      provider.handleAction('NAVIGATE_RETRIEVAL', {
        'results': [
          {
            'note_id': 's_1',
            'user_id': 'u1',
            'subject': 'Biology',
            'text': 'Mitosis cell division results in identical daughter cells.',
            'tag': 'Definition',
            'timestamp': '10:00 AM',
            'created_at': '2026-10-25T10:00:00',
            'updated_at': '2026-10-25T10:00:00',
          },
          {
            'note_id': 's_2',
            'user_id': 'u1',
            'subject': 'Geography',
            'text': 'Plate tectonics causes seismic fault activity.',
            'tag': 'Important',
            'timestamp': '10:15 AM',
            'created_at': '2026-10-25T10:15:00',
            'updated_at': '2026-10-25T10:15:00',
          }
        ],
        'query': 'mitosis',
        'current_index': 0,
      });

      expect(provider.searchResults.length, equals(2));
      expect(provider.searchQuery, equals('mitosis'));
      expect(provider.searchIndex, equals(0));
      expect(provider.currentSearchNote?.subject, equals('Biology'));

      provider.setSearchIndex(1);
      expect(provider.searchIndex, equals(1));
      expect(provider.currentSearchNote?.subject, equals('Geography'));

      provider.handleAction('AUDIO_INDEX_UPDATED', {'current_index': 0});
      expect(provider.searchIndex, equals(0));
    });
  });

  group('ApiClient Gemini Integration Tests', () {
    test('ApiClient contains valid baseUrl and handles error responses gracefully', () async {
      final client = ApiClient(baseUrl: 'http://127.0.0.1:9999');
      final settings = await client.getGeminiSettings();
      expect(settings, isNull);

      final updateRes = await client.updateGeminiKey('test_key');
      expect(updateRes, isNull);
    });
  });
}

