// Web implementation for Earcon audio cues using Web Audio API
// ignore: avoid_web_libraries_in_flutter
import 'dart:js' as js;

void playEarconNative(String type) {
  try {
    js.context.callMethod('playEarcon', [type]);
  } catch (e) {
    // Fail silently if Web Audio is not permitted or initialized yet
  }
}
