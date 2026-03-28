import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

const _localeKey = 'app_locale_code';

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError(
      'SharedPreferences must be overridden in bootstrap.');
});

class AppLocaleController extends StateNotifier<Locale> {
  AppLocaleController(this._prefs)
      : super(Locale(_prefs.getString(_localeKey) ?? 'en'));

  final SharedPreferences _prefs;

  Future<void> setLocale(String languageCode) async {
    state = Locale(languageCode);
    await _prefs.setString(_localeKey, languageCode);
  }
}

final appLocaleControllerProvider =
    StateNotifierProvider<AppLocaleController, Locale>((ref) {
  return AppLocaleController(ref.watch(sharedPreferencesProvider));
});
