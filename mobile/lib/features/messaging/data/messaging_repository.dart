import 'dart:io';

import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/messaging/domain/messaging_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final messagingRepositoryProvider = Provider<MessagingRepository>((ref) {
  return MessagingRepository(ref.watch(apiClientProvider));
});

class MessagingRepository {
  const MessagingRepository(this._client);

  final ApiClient _client;

  Future<ConversationPage> getInbox({
    required String accessToken,
    int page = 1,
    int pageSize = 20,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.conversations,
      accessToken: accessToken,
      query: {
        'page': page.toString(),
        'page_size': pageSize.toString(),
      },
    );
    return ConversationPage.fromJson(json);
  }

  Future<ConversationDetail> getConversation({
    required String accessToken,
    required String conversationId,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.conversation(conversationId),
      accessToken: accessToken,
    );
    return ConversationDetail.fromJson(json);
  }

  Future<ConversationDetail> createOrReopenFromListing({
    required String accessToken,
    required String listingId,
    String? initialMessage,
  }) async {
    final json = await _client.postMultipart(
      ApiEndpoints.conversationFromListing(listingId),
      accessToken: accessToken,
      files: const [],
      fileField: 'files',
      fields: {
        if (initialMessage != null && initialMessage.trim().isNotEmpty)
          'initial_message': initialMessage.trim(),
      },
    );
    return ConversationDetail.fromJson(json);
  }

  Future<MessageSendResponse> sendMessage({
    required String accessToken,
    required String conversationId,
    String? body,
    List<File> attachments = const [],
  }) async {
    final json = await _client.postMultipart(
      ApiEndpoints.conversationMessages(conversationId),
      accessToken: accessToken,
      files: attachments,
      fileField: 'files',
      fields: {
        if (body != null && body.trim().isNotEmpty) 'body': body.trim(),
      },
    );
    return MessageSendResponse.fromJson(json);
  }

  Future<void> markConversationRead({
    required String accessToken,
    required String conversationId,
  }) async {
    await _client.postJson(
      ApiEndpoints.conversationRead(conversationId),
      accessToken: accessToken,
    );
  }

  Future<File> downloadAttachment({
    required String accessToken,
    required String downloadUrl,
    required String fileName,
    required Directory directory,
  }) async {
    final bytes = await _client.getAbsoluteBytes(
      downloadUrl,
      accessToken: accessToken,
    );
    final safeName = fileName.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
    final file = File('${directory.path}/$safeName');
    await file.writeAsBytes(bytes, flush: true);
    return file;
  }
}
