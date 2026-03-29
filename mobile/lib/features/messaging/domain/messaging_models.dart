import 'package:electronics_marketplace_mobile/core/utils/json_parsers.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';

class ConversationCounterparty {
  const ConversationCounterparty({
    required this.publicId,
    required this.username,
    required this.fullName,
    this.profileImagePath,
  });

  final String publicId;
  final String username;
  final String fullName;
  final String? profileImagePath;

  factory ConversationCounterparty.fromJson(Map<String, dynamic> json) =>
      ConversationCounterparty(
        publicId: json['public_id'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        profileImagePath: json['profile_image_path'] as String?,
      );
}

class ConversationListing {
  const ConversationListing({
    required this.publicId,
    required this.title,
    required this.status,
    this.primaryMediaAssetKey,
  });

  final String publicId;
  final String title;
  final String status;
  final String? primaryMediaAssetKey;

  factory ConversationListing.fromJson(Map<String, dynamic> json) =>
      ConversationListing(
        publicId: json['public_id'] as String,
        title: json['title'] as String,
        status: json['status'] as String,
        primaryMediaAssetKey: json['primary_media_asset_key'] as String?,
      );
}

class MessageAttachment {
  const MessageAttachment({
    required this.publicId,
    required this.attachmentType,
    required this.fileName,
    required this.mimeType,
    required this.downloadUrl,
    this.fileSizeBytes,
  });

  final String publicId;
  final String attachmentType;
  final String fileName;
  final String mimeType;
  final String downloadUrl;
  final int? fileSizeBytes;

  bool get isImage => mimeType.startsWith('image/');

  factory MessageAttachment.fromJson(Map<String, dynamic> json) =>
      MessageAttachment(
        publicId: json['public_id'] as String,
        attachmentType: json['attachment_type'] as String,
        fileName: json['file_name'] as String,
        mimeType: json['mime_type'] as String,
        downloadUrl: json['download_url'] as String,
        fileSizeBytes: parseInt(json['file_size_bytes']),
      );
}

class ConversationMessage {
  const ConversationMessage({
    required this.publicId,
    required this.senderUserId,
    required this.messageType,
    required this.status,
    required this.createdAt,
    required this.attachments,
    this.body,
    this.readAt,
  });

  final String publicId;
  final String senderUserId;
  final String messageType;
  final String status;
  final DateTime createdAt;
  final DateTime? readAt;
  final String? body;
  final List<MessageAttachment> attachments;

  factory ConversationMessage.fromJson(Map<String, dynamic> json) =>
      ConversationMessage(
        publicId: json['public_id'] as String,
        senderUserId: json['sender_user_id'] as String,
        body: json['body'] as String?,
        messageType: json['message_type'] as String,
        status: json['status'] as String,
        readAt: json['read_at'] == null
            ? null
            : DateTime.parse(json['read_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        attachments: (json['attachments'] as List<dynamic>? ?? const [])
            .map((item) =>
                MessageAttachment.fromJson(item as Map<String, dynamic>))
            .toList(),
      );
}

class ConversationSummary {
  const ConversationSummary({
    required this.publicId,
    required this.status,
    required this.counterparty,
    required this.unreadCount,
    required this.updatedAt,
    this.listing,
    this.lastMessagePreview,
    this.lastMessageAt,
  });

  final String publicId;
  final String status;
  final ConversationCounterparty counterparty;
  final int unreadCount;
  final DateTime updatedAt;
  final ConversationListing? listing;
  final String? lastMessagePreview;
  final DateTime? lastMessageAt;

  factory ConversationSummary.fromJson(Map<String, dynamic> json) =>
      ConversationSummary(
        publicId: json['public_id'] as String,
        status: json['status'] as String,
        listing: json['listing'] == null
            ? null
            : ConversationListing.fromJson(
                json['listing'] as Map<String, dynamic>,
              ),
        counterparty: ConversationCounterparty.fromJson(
          json['counterparty'] as Map<String, dynamic>,
        ),
        unreadCount: parseInt(json['unread_count']) ?? 0,
        lastMessagePreview: json['last_message_preview'] as String?,
        lastMessageAt: json['last_message_at'] == null
            ? null
            : DateTime.parse(json['last_message_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}

class ConversationDetail {
  const ConversationDetail({
    required this.publicId,
    required this.status,
    required this.buyerUserId,
    required this.sellerUserId,
    required this.counterparty,
    required this.unreadCount,
    required this.messages,
    this.listing,
    this.lastMessageAt,
  });

  final String publicId;
  final String status;
  final String buyerUserId;
  final String sellerUserId;
  final ConversationCounterparty counterparty;
  final int unreadCount;
  final List<ConversationMessage> messages;
  final ConversationListing? listing;
  final DateTime? lastMessageAt;

  factory ConversationDetail.fromJson(Map<String, dynamic> json) =>
      ConversationDetail(
        publicId: json['public_id'] as String,
        status: json['status'] as String,
        listing: json['listing'] == null
            ? null
            : ConversationListing.fromJson(
                json['listing'] as Map<String, dynamic>,
              ),
        buyerUserId: json['buyer_user_id'] as String,
        sellerUserId: json['seller_user_id'] as String,
        counterparty: ConversationCounterparty.fromJson(
          json['counterparty'] as Map<String, dynamic>,
        ),
        unreadCount: parseInt(json['unread_count']) ?? 0,
        lastMessageAt: json['last_message_at'] == null
            ? null
            : DateTime.parse(json['last_message_at'] as String),
        messages: (json['messages'] as List<dynamic>? ?? const [])
            .map((item) =>
                ConversationMessage.fromJson(item as Map<String, dynamic>))
            .toList(),
      );
}

class ConversationPage {
  const ConversationPage({
    required this.items,
    required this.meta,
  });

  final List<ConversationSummary> items;
  final PaginationMeta meta;

  int get unreadCount => items.fold(0, (sum, item) => sum + item.unreadCount);

  factory ConversationPage.fromJson(Map<String, dynamic> json) =>
      ConversationPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) =>
                ConversationSummary.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class MessageSendResponse {
  const MessageSendResponse({
    required this.conversation,
    required this.message,
  });

  final ConversationDetail conversation;
  final ConversationMessage message;

  factory MessageSendResponse.fromJson(Map<String, dynamic> json) =>
      MessageSendResponse(
        conversation: ConversationDetail.fromJson(
          json['conversation'] as Map<String, dynamic>,
        ),
        message: ConversationMessage.fromJson(
          json['message'] as Map<String, dynamic>,
        ),
      );
}
