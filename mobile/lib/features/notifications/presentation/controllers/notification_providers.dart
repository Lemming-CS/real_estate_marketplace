import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/notifications/data/notifications_repository.dart';
import 'package:electronics_marketplace_mobile/features/notifications/domain/notification_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final notificationsProvider =
    FutureProvider.autoDispose<NotificationPage>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref
      .watch(notificationsRepositoryProvider)
      .getNotifications(accessToken: token);
});

final notificationUnreadCountProvider =
    FutureProvider.autoDispose<int>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    return 0;
  }
  return ref
      .watch(notificationsRepositoryProvider)
      .getUnreadCount(accessToken: token);
});
