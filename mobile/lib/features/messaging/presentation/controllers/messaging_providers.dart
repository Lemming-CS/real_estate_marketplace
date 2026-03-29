import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/messaging/data/messaging_repository.dart';
import 'package:electronics_marketplace_mobile/features/messaging/domain/messaging_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final inboxProvider = FutureProvider.autoDispose<ConversationPage>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref.watch(messagingRepositoryProvider).getInbox(accessToken: token);
});

final conversationDetailProvider =
    FutureProvider.autoDispose.family<ConversationDetail, String>(
  (ref, conversationId) async {
    final token = ref.watch(authControllerProvider).session?.accessToken;
    if (token == null) {
      throw StateError('Authentication required.');
    }
    return ref.watch(messagingRepositoryProvider).getConversation(
          accessToken: token,
          conversationId: conversationId,
        );
  },
);

final conversationUnreadBadgeProvider =
    FutureProvider.autoDispose<int>((ref) async {
  final page = await ref.watch(inboxProvider.future);
  return page.unreadCount;
});
