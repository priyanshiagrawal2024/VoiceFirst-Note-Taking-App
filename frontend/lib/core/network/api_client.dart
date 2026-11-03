import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../constants/constants.dart';
import '../models/note_model.dart';
import '../models/session_model.dart';
import '../models/flashcard_model.dart';

class ApiClient {
  String baseUrl;

  ApiClient({this.baseUrl = AppConstants.defaultBackendUrl});

  Future<Map<String, dynamic>> processVoice({
    required String text,
    Map<String, dynamic>? context,
    String userId = AppConstants.defaultUserId,
    double confidence = 1.0,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/voice/process'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'text': text,
          'user_id': userId,
          'confidence': confidence,
          'context': context ?? {},
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        return {
          'intent': 'ERROR',
          'spoken_response': "I couldn't reach the notes server. Please ensure the backend is running.",
          'action': 'none',
          'context': context ?? {},
        };
      }
    } catch (e) {
      return {
        'intent': 'NETWORK_ERROR',
        'spoken_response': "Connection error. Please check your backend server.",
        'action': 'none',
        'context': context ?? {},
      };
    }
  }

  Future<List<NoteModel>> getNotes({
    String userId = AppConstants.defaultUserId,
    String? subject,
    String? tag,
    String? timeframe,
  }) async {
    try {
      final queryParams = <String, String>{'user_id': userId};
      if (subject != null) queryParams['subject'] = subject;
      if (tag != null) queryParams['tag'] = tag;
      if (timeframe != null) queryParams['timeframe'] = timeframe;

      final uri = Uri.parse('$baseUrl/api/notes').replace(queryParameters: queryParams);
      final response = await http.get(uri);

      if (response.statusCode == 200) {
        final List list = jsonDecode(response.body);
        return list.map((item) => NoteModel.fromJson(item)).toList();
      }
    } catch (e) {
      // Return empty list on error
    }
    return [];
  }

  Future<NoteModel?> getLastNote({String userId = AppConstants.defaultUserId}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/notes/last?user_id=$userId'));
      if (response.statusCode == 200) {
        return NoteModel.fromJson(jsonDecode(response.body));
      }
    } catch (e) {}
    return null;
  }

  Future<bool> deleteNote(String noteId, {String userId = AppConstants.defaultUserId}) async {
    try {
      final response = await http.delete(Uri.parse('$baseUrl/api/notes/$noteId?user_id=$userId'));
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('[ApiClient] deleteNote error: $e');
      return false;
    }
  }

  Future<List<NoteModel>> searchNotes(String query, {String userId = AppConstants.defaultUserId}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/search').replace(queryParameters: {
        'user_id': userId,
        'q': query.trim(),
      });
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final List list = jsonDecode(response.body);
        return list.map((item) => NoteModel.fromJson(item)).toList();
      }
    } catch (e) {
      debugPrint('[ApiClient] searchNotes error: $e');
    }
    return [];
  }

  Future<Map<String, dynamic>> getAnalytics({String userId = AppConstants.defaultUserId}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/analytics?user_id=$userId'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data is Map<String, dynamic>) {
          if (data['analytics'] != null && data['analytics'] is Map) {
            return Map<String, dynamic>.from(data['analytics']);
          }
          return Map<String, dynamic>.from(data);
        }
      }
    } catch (e) {
      debugPrint('[ApiClient] getAnalytics error: $e');
    }
    return {};
  }

  Future<SessionModel?> getActiveSession({String userId = AppConstants.defaultUserId}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/sessions/active?user_id=$userId'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['is_active'] == true && data['session'] != null) {
          return SessionModel.fromJson(data['session']);
        }
      }
    } catch (e) {}
    return null;
  }

  Future<List<Map<String, dynamic>>> getBookmarks({String userId = AppConstants.defaultUserId}) async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/bookmarks?user_id=$userId'));
      if (response.statusCode == 200) {
        final List list = jsonDecode(response.body);
        return List<Map<String, dynamic>>.from(list);
      }
    } catch (e) {}
    return [];
  }

  Future<bool> checkHealth() async {
  try {
    final response = await http
        .get(Uri.parse('$baseUrl/api/health'))
        .timeout(const Duration(seconds: 60));

    return response.statusCode == 200;
  } catch (e) {
    debugPrint('[ApiClient] Health check error: $e');
    return false;
  }
}

  Future<List<FlashcardModel>> generateFlashcards({
    String userId = AppConstants.defaultUserId,
    String? topic,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/flashcards/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          if (topic != null && topic.trim().isNotEmpty) 'topic': topic.trim(),
        }),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final list = (data['cards'] ?? data['flashcards']) as List?;
        if (list != null) {
          return list.map((item) => FlashcardModel.fromJson(Map<String, dynamic>.from(item))).toList();
        }
      }
    } catch (e) {
      debugPrint("[ApiClient] generateFlashcards error: $e");
    }
    return [];
  }

  Future<List<QuizQuestionModel>> generateQuiz({
    String userId = AppConstants.defaultUserId,
    String? topic,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/quiz/generate'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          if (topic != null && topic.trim().isNotEmpty) 'topic': topic.trim(),
        }),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final list = (data['questions'] ?? data['quiz_items']) as List?;
        if (list != null) {
          return list.map((item) => QuizQuestionModel.fromJson(Map<String, dynamic>.from(item))).toList();
        }
      }
    } catch (e) {
      debugPrint("[ApiClient] generateQuiz error: $e");
    }
    return [];
  }

  Future<Map<String, dynamic>?> getGeminiSettings() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/settings/gemini_key'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint("[ApiClient] getGeminiSettings error: $e");
    }
    return null;
  }

  Future<Map<String, dynamic>?> updateGeminiKey(String apiKey) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/settings/gemini_key'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'api_key': apiKey}),
      );
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint("[ApiClient] updateGeminiKey error: $e");
    }
    return null;
  }
}

