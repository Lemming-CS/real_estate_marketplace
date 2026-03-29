// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get homeTitle => 'Real Estate Marketplace';

  @override
  String get homeSubtitle =>
      'Browse apartments and houses for rent or sale, message owners, and manage your property listings.';

  @override
  String get loginTitle => 'Sign in';

  @override
  String get loginSubtitle => 'Access your buyer or seller account.';

  @override
  String get backToHome => 'Back to home';

  @override
  String get apiBaseUrlLabel => 'API base URL';

  @override
  String get routingLabel => 'Routing';

  @override
  String get routingValue =>
      'go_router is configured for marketplace navigation.';

  @override
  String get scopeLabel => 'Current scope';

  @override
  String get scopeValue =>
      'Buyer, seller, admin-backed moderation, messaging, and promotion flows are implemented.';

  @override
  String get openLoginPlaceholder => 'Open sign-in';
}
