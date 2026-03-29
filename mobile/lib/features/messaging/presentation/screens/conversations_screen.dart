import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/controllers/messaging_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class ConversationsScreen extends ConsumerWidget {
  const ConversationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inboxAsync = ref.watch(inboxProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Inbox', 'Сообщения')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: inboxAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  context.tr(
                    'No conversations yet. Contact a seller from a property page to start chatting.',
                    'Пока нет диалогов. Напишите продавцу со страницы объекта, чтобы начать общение.',
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(inboxProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: page.items.length,
              itemBuilder: (context, index) {
                final conversation = page.items[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(12),
                    leading: conversation.listing?.primaryMediaAssetKey == null
                        ? CircleAvatar(
                            child: Text(
                              conversation
                                  .counterparty.fullName.characters.first
                                  .toUpperCase(),
                            ),
                          )
                        : ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: NetworkMediaImage(
                              assetKey:
                                  conversation.listing!.primaryMediaAssetKey!,
                              width: 56,
                              height: 56,
                            ),
                          ),
                    title: Text(conversation.counterparty.fullName),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (conversation.listing != null)
                          Text(
                            conversation.listing!.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        const SizedBox(height: 4),
                        Text(
                          conversation.lastMessagePreview ??
                              context.tr(
                                  'No messages yet.', 'Пока нет сообщений.'),
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _formatTimestamp(conversation.lastMessageAt),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                        if (conversation.unreadCount > 0) ...[
                          const SizedBox(height: 8),
                          CircleAvatar(
                            radius: 12,
                            child: Text(
                              '${conversation.unreadCount}',
                              style: Theme.of(context).textTheme.labelSmall,
                            ),
                          ),
                        ],
                      ],
                    ),
                    onTap: () =>
                        context.push('/conversations/${conversation.publicId}'),
                  ),
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(error.toString(), textAlign: TextAlign.center),
          ),
        ),
      ),
    );
  }

  String _formatTimestamp(DateTime? value) {
    if (value == null) {
      return '';
    }
    return DateFormat('MMM d, HH:mm').format(value.toLocal());
  }
}
