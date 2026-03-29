// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get homeTitle => 'Маркетплейс недвижимости';

  @override
  String get homeSubtitle =>
      'Просматривайте квартиры и дома для аренды и покупки, пишите владельцам и управляйте своими объектами.';

  @override
  String get loginTitle => 'Вход';

  @override
  String get loginSubtitle => 'Войдите в аккаунт покупателя или продавца.';

  @override
  String get backToHome => 'Вернуться на главную';

  @override
  String get apiBaseUrlLabel => 'Базовый URL API';

  @override
  String get routingLabel => 'Маршрутизация';

  @override
  String get routingValue =>
      'go_router уже настроен для навигации по маркетплейсу.';

  @override
  String get scopeLabel => 'Текущий объем';

  @override
  String get scopeValue =>
      'Реализованы сценарии покупателя, продавца, модерации, переписки и продвижения.';

  @override
  String get openLoginPlaceholder => 'Открыть вход';
}
