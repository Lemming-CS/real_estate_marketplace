import 'dart:math';

import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _guestTokenKey = 'guest_viewer_token';

class GuestTokenStorage {
  GuestTokenStorage(this._prefs);

  final SharedPreferences _prefs;

  Future<String> readOrCreate() async {
    final existing = _prefs.getString(_guestTokenKey);
    if (existing != null && existing.isNotEmpty) {
      return existing;
    }

    final token = _generateToken();
    await _prefs.setString(_guestTokenKey, token);
    return token;
  }

  String _generateToken() {
    final random = Random.secure();
    final buffer = StringBuffer();
    for (var index = 0; index < 32; index += 1) {
      buffer.write(random.nextInt(256).toRadixString(16).padLeft(2, '0'));
    }
    return buffer.toString();
  }
}

final guestTokenStorageProvider = Provider<GuestTokenStorage>((ref) {
  return GuestTokenStorage(ref.watch(sharedPreferencesProvider));
});

final guestTokenProvider = FutureProvider<String>((ref) async {
  return ref.watch(guestTokenStorageProvider).readOrCreate();
});
