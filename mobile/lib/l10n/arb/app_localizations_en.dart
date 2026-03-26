// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get homeTitle => 'Starter Home';

  @override
  String get homeSubtitle =>
      'This Flutter app is wired for routing, localization, and environment-based configuration. Marketplace features will land in later stages.';

  @override
  String get loginTitle => 'Login Placeholder';

  @override
  String get loginSubtitle =>
      'Authentication UI is intentionally deferred until backend auth endpoints are implemented.';

  @override
  String get backToHome => 'Back to home';

  @override
  String get apiBaseUrlLabel => 'API base URL';

  @override
  String get routingLabel => 'Routing';

  @override
  String get routingValue => 'go_router is configured for the starter screens.';

  @override
  String get scopeLabel => 'Current scope';

  @override
  String get scopeValue =>
      'Scaffold only. Buyer and seller flows are still ahead.';

  @override
  String get openLoginPlaceholder => 'Open login placeholder';
}
