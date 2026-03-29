import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/reports/domain/report_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final reportsRepositoryProvider = Provider<ReportsRepository>((ref) {
  return ReportsRepository(ref.watch(apiClientProvider));
});

class ReportsRepository {
  const ReportsRepository(this._client);

  final ApiClient _client;

  Future<ReportItem> createListingReport({
    required String accessToken,
    required String listingId,
    required String reasonCode,
    String? description,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.reports,
      accessToken: accessToken,
      body: {
        'listing_public_id': listingId,
        'reason_code': reasonCode.trim(),
        'description':
            description?.trim().isEmpty == true ? null : description?.trim(),
      },
    );
    return ReportItem.fromJson(json);
  }

  Future<ReportItem> createConversationReport({
    required String accessToken,
    required String conversationId,
    required String reasonCode,
    String? description,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.reports,
      accessToken: accessToken,
      body: {
        'conversation_public_id': conversationId,
        'reason_code': reasonCode.trim(),
        'description':
            description?.trim().isEmpty == true ? null : description?.trim(),
      },
    );
    return ReportItem.fromJson(json);
  }

  Future<ReportPage> getMyReports({
    required String accessToken,
    int page = 1,
    int pageSize = 20,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.myReports,
      accessToken: accessToken,
      query: {'page': '$page', 'page_size': '$pageSize'},
    );
    return ReportPage.fromJson(json);
  }
}
