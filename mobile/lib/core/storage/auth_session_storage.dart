import 'dart:convert';

import 'package:electronics_marketplace_mobile/features/auth/domain/auth_models.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AuthSessionStorage {
  AuthSessionStorage(this._prefs);

  static const _sessionKey = 'auth_session';

  final SharedPreferences _prefs;

  AuthSession? read() {
    final raw = _prefs.getString(_sessionKey);
    if (raw == null || raw.isEmpty) {
      return null;
    }
    return AuthSession.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }

  Future<void> write(AuthSession session) {
    return _prefs.setString(_sessionKey, jsonEncode(session.toJson()));
  }

  Future<void> clear() {
    return _prefs.remove(_sessionKey);
  }
}
