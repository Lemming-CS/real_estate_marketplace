import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/notifications/domain/notification_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final notificationsRepositoryProvider =
    Provider<NotificationsRepository>((ref) {
  return NotificationsRepository(ref.watch(apiClientProvider));
});

class NotificationsRepository {
  const NotificationsRepository(this._client);

  final ApiClient _client;

  Future<NotificationPage> getNotifications({
    required String accessToken,
    int page = 1,
    int pageSize = 20,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.notifications,
      accessToken: accessToken,
      query: {
        'page': page.toString(),
        'page_size': pageSize.toString(),
      },
    );
    return NotificationPage.fromJson(json);
  }

  Future<int> getUnreadCount({
    required String accessToken,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.notificationUnreadCount,
      accessToken: accessToken,
    );
    return (json['unread_count'] as num?)?.toInt() ?? 0;
  }

  Future<AppNotification> markRead({
    required String accessToken,
    required int notificationId,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.notificationRead(notificationId),
      accessToken: accessToken,
    );
    return AppNotification.fromJson(json);
  }
}
