import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/commerce/domain/commerce_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final commerceRepositoryProvider = Provider<CommerceRepository>((ref) {
  return CommerceRepository(ref.watch(apiClientProvider));
});

class CommerceRepository {
  const CommerceRepository(this._client);

  final ApiClient _client;

  Future<List<PromotionPackage>> getPromotionPackages() async {
    final json = await _client.getJsonList(ApiEndpoints.promotionPackages);
    return json
        .map((item) => PromotionPackage.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<PaymentPage> getPayments({
    required String accessToken,
    int page = 1,
    int pageSize = 20,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.payments,
      accessToken: accessToken,
      query: {'page': '$page', 'page_size': '$pageSize'},
    );
    return PaymentPage.fromJson(json);
  }

  Future<PromotionPage> getPromotions({
    required String accessToken,
    int page = 1,
    int pageSize = 20,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.promotionsMe,
      accessToken: accessToken,
      query: {'page': '$page', 'page_size': '$pageSize'},
    );
    return PromotionPage.fromJson(json);
  }

  Future<PromotionInitiationResult> initiatePromotion({
    required String accessToken,
    required String listingId,
    required String packageId,
    required int durationDays,
    String? targetCity,
    String? targetCategoryPublicId,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.paymentPromotionInitiate,
      accessToken: accessToken,
      body: {
        'listing_public_id': listingId,
        'package_public_id': packageId,
        'duration_days': durationDays,
        'target_city': targetCity,
        'target_category_public_id': targetCategoryPublicId,
      },
    );
    return PromotionInitiationResult.fromJson(json);
  }

  Future<PaymentSimulationResult> completeMockCheckout({
    required String accessToken,
    required String checkoutUrl,
  }) async {
    final json = await _client.getAbsoluteJson(
      checkoutUrl,
      accessToken: accessToken,
    );
    return PaymentSimulationResult.fromJson(json);
  }
}
