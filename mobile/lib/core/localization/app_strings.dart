import 'package:flutter/widgets.dart';

extension AppStringsX on BuildContext {
  bool get isRussian => Localizations.localeOf(this).languageCode == 'ru';

  String tr(String en, String ru) => isRussian ? ru : en;
}
