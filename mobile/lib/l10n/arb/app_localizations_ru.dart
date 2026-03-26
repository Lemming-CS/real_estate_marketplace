// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Russian (`ru`).
class AppLocalizationsRu extends AppLocalizations {
  AppLocalizationsRu([String locale = 'ru']) : super(locale);

  @override
  String get homeTitle => 'Стартовый экран';

  @override
  String get homeSubtitle =>
      'Это Flutter-приложение уже настроено для маршрутизации, локализации и конфигурации через переменные окружения. Функции маркетплейса будут добавлены позже.';

  @override
  String get loginTitle => 'Заглушка входа';

  @override
  String get loginSubtitle =>
      'Интерфейс аутентификации отложен до появления backend-эндпоинтов входа.';

  @override
  String get backToHome => 'Вернуться на главную';

  @override
  String get apiBaseUrlLabel => 'Базовый URL API';

  @override
  String get routingLabel => 'Маршрутизация';

  @override
  String get routingValue => 'Для стартовых экранов уже настроен go_router.';

  @override
  String get scopeLabel => 'Текущий объем';

  @override
  String get scopeValue =>
      'Пока это только каркас. Сценарии покупателя и продавца будут реализованы позже.';

  @override
  String get openLoginPlaceholder => 'Открыть заглушку входа';
}
