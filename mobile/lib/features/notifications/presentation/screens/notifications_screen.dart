import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/controllers/messaging_providers.dart';
import 'package:electronics_marketplace_mobile/features/notifications/data/notifications_repository.dart';
import 'package:electronics_marketplace_mobile/features/notifications/domain/notification_models.dart';
import 'package:electronics_marketplace_mobile/features/notifications/presentation/controllers/notification_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notificationsAsync = ref.watch(notificationsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Notifications', 'Уведомления')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: notificationsAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
              child: Text(
                context.tr(
                  'No notifications yet.',
                  'Пока нет уведомлений.',
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(notificationsProvider);
              ref.invalidate(notificationUnreadCountProvider);
            },
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: page.items.length,
              itemBuilder: (context, index) {
                final item = page.items[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(12),
                    leading: CircleAvatar(
                      child: Icon(_iconFor(item.notificationType)),
                    ),
                    title: Text(item.title),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 4),
                        Text(item.body),
                        const SizedBox(height: 6),
                        Text(
                          DateFormat('MMM d, HH:mm')
                              .format(item.createdAt.toLocal()),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ],
                    ),
                    trailing: item.isUnread
                        ? Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.primary,
                              shape: BoxShape.circle,
                            ),
                          )
                        : null,
                    onTap: () => _openNotification(context, ref, item),
                  ),
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text(error.toString())),
      ),
    );
  }

  Future<void> _openNotification(
    BuildContext context,
    WidgetRef ref,
    AppNotification item,
  ) async {
    final accessToken = ref.read(authControllerProvider).session?.accessToken;
    if (accessToken == null) {
      return;
    }
    if (item.isUnread) {
      await ref.read(notificationsRepositoryProvider).markRead(
            accessToken: accessToken,
            notificationId: item.id,
          );
      ref.invalidate(notificationsProvider);
      ref.invalidate(notificationUnreadCountProvider);
      ref.invalidate(inboxProvider);
      ref.invalidate(conversationUnreadBadgeProvider);
    }

    final data = item.data;
    if (data is Map<String, dynamic>) {
      final conversationId = data['conversation_public_id'] as String?;
      final listingId = data['listing_public_id'] as String?;
      if (conversationId != null && context.mounted) {
        context.push('/conversations/$conversationId');
        return;
      }
      if (listingId != null && context.mounted) {
        context.push('/listing/$listingId');
        return;
      }
    }
  }

  IconData _iconFor(String type) {
    if (type.startsWith('message')) {
      return Icons.chat_bubble_outline;
    }
    if (type.startsWith('payment')) {
      return Icons.receipt_long_outlined;
    }
    if (type.startsWith('promotion')) {
      return Icons.workspace_premium_outlined;
    }
    return Icons.notifications_none;
  }
}
