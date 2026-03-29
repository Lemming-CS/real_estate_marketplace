import 'package:electronics_marketplace_mobile/core/auth/session_expiry_notifier.dart';
import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient(
    baseUrl: AppConfig.apiBaseUrl,
    onUnauthorized: ref.watch(sessionExpiryNotifierProvider).notify,
  );
});
