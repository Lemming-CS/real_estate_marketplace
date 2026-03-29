import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';

class ReportItem {
  const ReportItem({
    required this.publicId,
    required this.reporterUserPublicId,
    required this.reporterUsername,
    required this.reasonCode,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.reportedUserPublicId,
    this.reportedUsername,
    this.conversationPublicId,
    this.listingPublicId,
    this.listingTitle,
    this.listingStatus,
    this.listingModerationNote,
    this.description,
    this.reportedUserStatus,
    this.resolutionNote,
    this.resolvedAt,
  });

  final String publicId;
  final String reporterUserPublicId;
  final String reporterUsername;
  final String? reportedUserPublicId;
  final String? reportedUsername;
  final String? conversationPublicId;
  final String? listingPublicId;
  final String? listingTitle;
  final String? listingStatus;
  final String? listingModerationNote;
  final String reasonCode;
  final String? description;
  final String? reportedUserStatus;
  final String status;
  final String? resolutionNote;
  final DateTime? resolvedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ReportItem.fromJson(Map<String, dynamic> json) => ReportItem(
        publicId: json['public_id'] as String,
        reporterUserPublicId: json['reporter_user_public_id'] as String,
        reporterUsername: json['reporter_username'] as String,
        reportedUserPublicId: json['reported_user_public_id'] as String?,
        reportedUsername: json['reported_username'] as String?,
        conversationPublicId: json['conversation_public_id'] as String?,
        listingPublicId: json['listing_public_id'] as String?,
        listingTitle: json['listing_title'] as String?,
        listingStatus: json['listing_status'] as String?,
        listingModerationNote: json['listing_moderation_note'] as String?,
        reasonCode: json['reason_code'] as String,
        description: json['description'] as String?,
        reportedUserStatus: json['reported_user_status'] as String?,
        status: json['status'] as String,
        resolutionNote: json['resolution_note'] as String?,
        resolvedAt: json['resolved_at'] == null
            ? null
            : DateTime.parse(json['resolved_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );
}

class ReportPage {
  const ReportPage({
    required this.items,
    required this.meta,
  });

  final List<ReportItem> items;
  final PaginationMeta meta;

  factory ReportPage.fromJson(Map<String, dynamic> json) => ReportPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) => ReportItem.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}
