import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';

class AppNotification {
  const AppNotification({
    required this.id,
    required this.notificationType,
    required this.title,
    required this.body,
    required this.status,
    required this.createdAt,
    this.data,
    this.readAt,
  });

  final int id;
  final String notificationType;
  final String title;
  final String body;
  final String status;
  final DateTime createdAt;
  final DateTime? readAt;
  final Object? data;

  bool get isUnread => readAt == null && status != 'read';

  factory AppNotification.fromJson(Map<String, dynamic> json) =>
      AppNotification(
        id: json['id'] as int,
        notificationType: json['notification_type'] as String,
        title: json['title'] as String,
        body: json['body'] as String,
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        readAt: json['read_at'] == null
            ? null
            : DateTime.parse(json['read_at'] as String),
        data: json['data_json'],
      );
}

class NotificationPage {
  const NotificationPage({
    required this.items,
    required this.meta,
  });

  final List<AppNotification> items;
  final PaginationMeta meta;

  factory NotificationPage.fromJson(Map<String, dynamic> json) =>
      NotificationPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) =>
                AppNotification.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}
