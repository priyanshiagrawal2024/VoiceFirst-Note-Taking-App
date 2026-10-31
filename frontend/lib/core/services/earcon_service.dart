import 'earcon_stub.dart'
    if (dart.library.js) 'earcon_web.dart' as impl;

/// EarconService provides non-visual acoustic cues (earcons) for visually impaired users.
/// Typical earcons:
/// - 'listen_start': High rising tone indicating microphone is listening.
/// - 'processing': Gentle descending tone indicating voice is being processed.
/// - 'correct': Cheerful ascending chime for correct answer.
/// - 'incorrect': Low tone for incorrect answer.
class EarconService {
  static void play(String type) {
    try {
      impl.playEarconNative(type);
    } catch (_) {}
  }
}
