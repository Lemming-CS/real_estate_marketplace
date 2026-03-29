import 'package:electronics_marketplace_mobile/core/utils/json_parsers.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';

class PromotionPackage {
  const PromotionPackage({
    required this.publicId,
    required this.code,
    required this.name,
    required this.durationDays,
    required this.priceAmount,
    required this.currencyCode,
    required this.boostLevel,
    required this.status,
    this.description,
  });

  final String publicId;
  final String code;
  final String name;
  final int durationDays;
  final String priceAmount;
  final String currencyCode;
  final int boostLevel;
  final String status;
  final String? description;

  bool get isActive => status == 'active';

  factory PromotionPackage.fromJson(Map<String, dynamic> json) =>
      PromotionPackage(
        publicId: json['public_id'] as String,
        code: json['code'] as String,
        name: json['name'] as String,
        description: json['description'] as String?,
        durationDays: parseInt(json['duration_days']) ?? 0,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        boostLevel: parseInt(json['boost_level']) ?? 0,
        status: json['status'] as String,
      );
}

class PaymentRecordItem {
  const PaymentRecordItem({
    required this.publicId,
    required this.paymentType,
    required this.provider,
    required this.amount,
    required this.currencyCode,
    required this.status,
    required this.createdAt,
    this.providerReference,
    this.failureReason,
    this.listingPublicId,
    this.listingTitle,
    this.promotionPublicId,
    this.checkoutUrl,
    this.paidAt,
    this.failedAt,
    this.cancelledAt,
    this.refundedReadyAt,
  });

  final String publicId;
  final String paymentType;
  final String provider;
  final String amount;
  final String currencyCode;
  final String status;
  final DateTime createdAt;
  final String? providerReference;
  final String? failureReason;
  final String? listingPublicId;
  final String? listingTitle;
  final String? promotionPublicId;
  final String? checkoutUrl;
  final DateTime? paidAt;
  final DateTime? failedAt;
  final DateTime? cancelledAt;
  final DateTime? refundedReadyAt;

  factory PaymentRecordItem.fromJson(Map<String, dynamic> json) =>
      PaymentRecordItem(
        publicId: json['public_id'] as String,
        paymentType: json['payment_type'] as String,
        provider: json['provider'] as String,
        providerReference: json['provider_reference'] as String?,
        amount: (parseDouble(json['amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        status: json['status'] as String,
        failureReason: json['failure_reason'] as String?,
        listingPublicId: json['listing_public_id'] as String?,
        listingTitle: json['listing_title'] as String?,
        promotionPublicId: json['promotion_public_id'] as String?,
        checkoutUrl: json['checkout_url'] as String?,
        paidAt: json['paid_at'] == null
            ? null
            : DateTime.parse(json['paid_at'] as String),
        failedAt: json['failed_at'] == null
            ? null
            : DateTime.parse(json['failed_at'] as String),
        cancelledAt: json['cancelled_at'] == null
            ? null
            : DateTime.parse(json['cancelled_at'] as String),
        refundedReadyAt: json['refunded_ready_at'] == null
            ? null
            : DateTime.parse(json['refunded_ready_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class PromotionRecord {
  const PromotionRecord({
    required this.publicId,
    required this.listingPublicId,
    required this.listingTitle,
    required this.packagePublicId,
    required this.packageCode,
    required this.packageName,
    required this.status,
    required this.durationDays,
    required this.priceAmount,
    required this.currencyCode,
    required this.createdAt,
    this.targetCity,
    this.targetCategoryPublicId,
    this.targetCategoryName,
    this.paymentPublicId,
    this.startsAt,
    this.endsAt,
    this.activatedAt,
    this.cancelledAt,
  });

  final String publicId;
  final String listingPublicId;
  final String listingTitle;
  final String packagePublicId;
  final String packageCode;
  final String packageName;
  final String status;
  final String? targetCity;
  final String? targetCategoryPublicId;
  final String? targetCategoryName;
  final int durationDays;
  final String priceAmount;
  final String currencyCode;
  final String? paymentPublicId;
  final DateTime? startsAt;
  final DateTime? endsAt;
  final DateTime? activatedAt;
  final DateTime? cancelledAt;
  final DateTime createdAt;

  factory PromotionRecord.fromJson(Map<String, dynamic> json) =>
      PromotionRecord(
        publicId: json['public_id'] as String,
        listingPublicId: json['listing_public_id'] as String,
        listingTitle: json['listing_title'] as String,
        packagePublicId: json['package_public_id'] as String,
        packageCode: json['package_code'] as String,
        packageName: json['package_name'] as String,
        status: json['status'] as String,
        targetCity: json['target_city'] as String?,
        targetCategoryPublicId: json['target_category_public_id'] as String?,
        targetCategoryName: json['target_category_name'] as String?,
        durationDays: parseInt(json['duration_days']) ?? 0,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        paymentPublicId: json['payment_public_id'] as String?,
        startsAt: json['starts_at'] == null
            ? null
            : DateTime.parse(json['starts_at'] as String),
        endsAt: json['ends_at'] == null
            ? null
            : DateTime.parse(json['ends_at'] as String),
        activatedAt: json['activated_at'] == null
            ? null
            : DateTime.parse(json['activated_at'] as String),
        cancelledAt: json['cancelled_at'] == null
            ? null
            : DateTime.parse(json['cancelled_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

class PaymentPriceBreakdown {
  const PaymentPriceBreakdown({
    required this.baseDurationDays,
    required this.selectedDurationDays,
    required this.basePriceAmount,
    required this.totalAmount,
    required this.currencyCode,
  });

  final int baseDurationDays;
  final int selectedDurationDays;
  final String basePriceAmount;
  final String totalAmount;
  final String currencyCode;

  factory PaymentPriceBreakdown.fromJson(Map<String, dynamic> json) =>
      PaymentPriceBreakdown(
        baseDurationDays: parseInt(json['base_duration_days']) ?? 0,
        selectedDurationDays: parseInt(json['selected_duration_days']) ?? 0,
        basePriceAmount:
            (parseDouble(json['base_price_amount']) ?? 0).toString(),
        totalAmount: (parseDouble(json['total_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
      );
}

class PromotionInitiationResult {
  const PromotionInitiationResult({
    required this.payment,
    required this.promotion,
    required this.priceBreakdown,
  });

  final PaymentRecordItem payment;
  final PromotionRecord promotion;
  final PaymentPriceBreakdown priceBreakdown;

  factory PromotionInitiationResult.fromJson(Map<String, dynamic> json) =>
      PromotionInitiationResult(
        payment: PaymentRecordItem.fromJson(
          json['payment'] as Map<String, dynamic>,
        ),
        promotion: PromotionRecord.fromJson(
          json['promotion'] as Map<String, dynamic>,
        ),
        priceBreakdown: PaymentPriceBreakdown.fromJson(
          json['price_breakdown'] as Map<String, dynamic>,
        ),
      );
}

class PaymentSimulationResult {
  const PaymentSimulationResult({
    required this.payment,
    this.promotion,
  });

  final PaymentRecordItem payment;
  final PromotionRecord? promotion;

  factory PaymentSimulationResult.fromJson(Map<String, dynamic> json) =>
      PaymentSimulationResult(
        payment: PaymentRecordItem.fromJson(
          json['payment'] as Map<String, dynamic>,
        ),
        promotion: json['promotion'] == null
            ? null
            : PromotionRecord.fromJson(
                json['promotion'] as Map<String, dynamic>,
              ),
      );
}

class PaymentPage {
  const PaymentPage({
    required this.items,
    required this.meta,
  });

  final List<PaymentRecordItem> items;
  final PaginationMeta meta;

  factory PaymentPage.fromJson(Map<String, dynamic> json) => PaymentPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) =>
                PaymentRecordItem.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class PromotionPage {
  const PromotionPage({
    required this.items,
    required this.meta,
  });

  final List<PromotionRecord> items;
  final PaginationMeta meta;

  factory PromotionPage.fromJson(Map<String, dynamic> json) => PromotionPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) =>
                PromotionRecord.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}
