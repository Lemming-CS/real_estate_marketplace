import 'package:flutter_dotenv/flutter_dotenv.dart';

class AppConfig {
  static String get appName =>
      dotenv.env['APP_NAME'] ?? 'Real Estate Marketplace';

  static String get apiBaseUrl =>
      dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000/api/v1';
}
