import 'package:electronics_marketplace_mobile/core/utils/json_parsers.dart';

class PaginationMeta {
  const PaginationMeta({
    required this.page,
    required this.pageSize,
    required this.totalItems,
    required this.totalPages,
  });

  final int page;
  final int pageSize;
  final int totalItems;
  final int totalPages;

  factory PaginationMeta.fromJson(Map<String, dynamic> json) => PaginationMeta(
        page: parseInt(json['page']) ?? 1,
        pageSize: parseInt(json['page_size']) ?? 20,
        totalItems: parseInt(json['total_items']) ?? 0,
        totalPages: parseInt(json['total_pages']) ?? 0,
      );
}

class ListingCategorySummary {
  const ListingCategorySummary({
    required this.publicId,
    required this.slug,
    required this.name,
  });

  final String publicId;
  final String slug;
  final String name;

  factory ListingCategorySummary.fromJson(Map<String, dynamic> json) =>
      ListingCategorySummary(
        publicId: json['public_id'] as String,
        slug: json['slug'] as String,
        name: json['name'] as String,
      );
}

class SellerSummary {
  const SellerSummary({
    required this.publicId,
    required this.username,
    required this.fullName,
    this.profileImagePath,
  });

  final String publicId;
  final String username;
  final String fullName;
  final String? profileImagePath;

  factory SellerSummary.fromJson(Map<String, dynamic> json) => SellerSummary(
        publicId: json['public_id'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        profileImagePath: json['profile_image_path'] as String?,
      );
}

class ListingMedia {
  const ListingMedia({
    required this.publicId,
    required this.mediaType,
    required this.assetKey,
    required this.mimeType,
    required this.sortOrder,
    required this.isPrimary,
    this.fileSizeBytes,
  });

  final String publicId;
  final String mediaType;
  final String assetKey;
  final String mimeType;
  final int sortOrder;
  final bool isPrimary;
  final int? fileSizeBytes;

  bool get isVideo => mediaType == 'video';

  factory ListingMedia.fromJson(Map<String, dynamic> json) => ListingMedia(
        publicId: json['public_id'] as String,
        mediaType: json['media_type'] as String,
        assetKey: json['asset_key'] as String,
        mimeType: json['mime_type'] as String,
        sortOrder: parseInt(json['sort_order']) ?? 0,
        isPrimary: json['is_primary'] as bool? ?? false,
        fileSizeBytes: parseInt(json['file_size_bytes']),
      );
}

class ListingAttributeValue {
  const ListingAttributeValue({
    required this.attributeCode,
    required this.displayName,
    required this.dataType,
    this.unit,
    this.textValue,
    this.numericValue,
    this.booleanValue,
    this.optionValue,
  });

  final String attributeCode;
  final String displayName;
  final String dataType;
  final String? unit;
  final String? textValue;
  final double? numericValue;
  final bool? booleanValue;
  final String? optionValue;

  factory ListingAttributeValue.fromJson(Map<String, dynamic> json) =>
      ListingAttributeValue(
        attributeCode: json['attribute_code'] as String,
        displayName: json['display_name'] as String,
        dataType: json['data_type'] as String,
        unit: json['unit'] as String?,
        textValue: json['text_value'] as String?,
        numericValue: parseDouble(json['numeric_value']),
        booleanValue: json['boolean_value'] as bool?,
        optionValue: json['option_value'] as String?,
      );
}

class ListingPromotionState {
  const ListingPromotionState({
    required this.publicId,
    required this.packageName,
    required this.packageCode,
    required this.status,
    required this.durationDays,
    required this.priceAmount,
    required this.currencyCode,
    this.targetCity,
    this.targetCategoryPublicId,
    this.targetCategoryName,
    this.startsAt,
    this.endsAt,
    this.activatedAt,
  });

  final String publicId;
  final String packageName;
  final String? packageCode;
  final String status;
  final int durationDays;
  final String priceAmount;
  final String? currencyCode;
  final String? targetCity;
  final String? targetCategoryPublicId;
  final String? targetCategoryName;
  final DateTime? startsAt;
  final DateTime? endsAt;
  final DateTime? activatedAt;

  factory ListingPromotionState.fromJson(Map<String, dynamic> json) =>
      ListingPromotionState(
        publicId: json['public_id'] as String,
        packageName: json['package_name'] as String,
        packageCode: json['package_code'] as String?,
        status: json['status'] as String,
        durationDays: parseInt(json['duration_days']) ?? 0,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String?,
        targetCity: json['target_city'] as String?,
        targetCategoryPublicId: json['target_category_public_id'] as String?,
        targetCategoryName: json['target_category_name'] as String?,
        startsAt: json['starts_at'] == null
            ? null
            : DateTime.parse(json['starts_at'] as String),
        endsAt: json['ends_at'] == null
            ? null
            : DateTime.parse(json['ends_at'] as String),
        activatedAt: json['activated_at'] == null
            ? null
            : DateTime.parse(json['activated_at'] as String),
      );
}

class OwnerCard {
  const OwnerCard({
    required this.publicId,
    required this.username,
    required this.fullName,
    required this.createdAt,
    required this.activeListingCount,
    this.bio,
    this.profileImagePath,
  });

  final String publicId;
  final String username;
  final String fullName;
  final DateTime createdAt;
  final int activeListingCount;
  final String? bio;
  final String? profileImagePath;

  factory OwnerCard.fromJson(Map<String, dynamic> json) => OwnerCard(
        publicId: json['public_id'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        activeListingCount: parseInt(json['active_listing_count']) ?? 0,
        bio: json['bio'] as String?,
        profileImagePath: json['profile_image_path'] as String?,
      );
}

class ListingSummary {
  const ListingSummary({
    required this.publicId,
    required this.title,
    required this.purpose,
    required this.propertyType,
    required this.priceAmount,
    required this.currencyCode,
    required this.status,
    required this.city,
    required this.latitude,
    required this.longitude,
    required this.roomCount,
    required this.areaSqm,
    required this.category,
    required this.seller,
    required this.isPromoted,
    required this.favoritesCount,
    required this.viewCount,
    this.promotionState,
    this.district,
    this.mapLabel,
    this.floor,
    this.totalFloors,
    this.furnished,
    this.primaryMedia,
  });

  final String publicId;
  final String title;
  final String purpose;
  final String propertyType;
  final String priceAmount;
  final String currencyCode;
  final String status;
  final String city;
  final String? district;
  final String? mapLabel;
  final double latitude;
  final double longitude;
  final int roomCount;
  final String areaSqm;
  final int? floor;
  final int? totalFloors;
  final bool? furnished;
  final ListingCategorySummary category;
  final SellerSummary seller;
  final ListingMedia? primaryMedia;
  final int favoritesCount;
  final int viewCount;
  final bool isPromoted;
  final ListingPromotionState? promotionState;

  factory ListingSummary.fromJson(Map<String, dynamic> json) => ListingSummary(
        publicId: json['public_id'] as String,
        title: json['title'] as String,
        purpose: json['purpose'] as String,
        propertyType: json['property_type'] as String,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        status: json['status'] as String,
        city: json['city'] as String,
        district: json['district'] as String?,
        mapLabel: json['map_label'] as String?,
        latitude: parseDouble(json['latitude']) ?? 0,
        longitude: parseDouble(json['longitude']) ?? 0,
        roomCount: parseInt(json['room_count']) ?? 0,
        areaSqm: (parseDouble(json['area_sqm']) ?? 0).toString(),
        floor: parseInt(json['floor']),
        totalFloors: parseInt(json['total_floors']),
        furnished: json['furnished'] as bool?,
        category: ListingCategorySummary.fromJson(
            json['category'] as Map<String, dynamic>),
        seller: SellerSummary.fromJson(json['seller'] as Map<String, dynamic>),
        primaryMedia: json['primary_media'] == null
            ? null
            : ListingMedia.fromJson(
                json['primary_media'] as Map<String, dynamic>),
        favoritesCount: parseInt(json['favorites_count']) ?? 0,
        viewCount: parseInt(json['view_count']) ?? 0,
        isPromoted: json['is_promoted'] as bool? ?? false,
        promotionState: json['promotion_state'] == null
            ? null
            : ListingPromotionState.fromJson(
                json['promotion_state'] as Map<String, dynamic>,
              ),
      );
}

class ListingDetail extends ListingSummary {
  const ListingDetail({
    required super.publicId,
    required super.title,
    required super.purpose,
    required super.propertyType,
    required super.priceAmount,
    required super.currencyCode,
    required super.status,
    required super.city,
    required super.latitude,
    required super.longitude,
    required super.roomCount,
    required super.areaSqm,
    required super.category,
    required super.seller,
    required super.isPromoted,
    required super.favoritesCount,
    required super.viewCount,
    required this.description,
    required this.addressText,
    required this.owner,
    required this.mediaItems,
    required this.attributeValues,
    this.moderationNote,
    super.district,
    super.mapLabel,
    super.floor,
    super.totalFloors,
    super.furnished,
    super.primaryMedia,
    super.promotionState,
  });

  final String description;
  final String addressText;
  final OwnerCard owner;
  final List<ListingMedia> mediaItems;
  final List<ListingAttributeValue> attributeValues;
  final String? moderationNote;

  factory ListingDetail.fromJson(Map<String, dynamic> json) => ListingDetail(
        publicId: json['public_id'] as String,
        title: json['title'] as String,
        purpose: json['purpose'] as String,
        propertyType: json['property_type'] as String,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        status: json['status'] as String,
        city: json['city'] as String,
        district: json['district'] as String?,
        mapLabel: json['map_label'] as String?,
        latitude: parseDouble(json['latitude']) ?? 0,
        longitude: parseDouble(json['longitude']) ?? 0,
        roomCount: parseInt(json['room_count']) ?? 0,
        areaSqm: (parseDouble(json['area_sqm']) ?? 0).toString(),
        floor: parseInt(json['floor']),
        totalFloors: parseInt(json['total_floors']),
        furnished: json['furnished'] as bool?,
        category: ListingCategorySummary.fromJson(
            json['category'] as Map<String, dynamic>),
        seller: SellerSummary.fromJson(json['seller'] as Map<String, dynamic>),
        primaryMedia: json['primary_media'] == null
            ? null
            : ListingMedia.fromJson(
                json['primary_media'] as Map<String, dynamic>),
        favoritesCount: parseInt(json['favorites_count']) ?? 0,
        viewCount: parseInt(json['view_count']) ?? 0,
        isPromoted: json['is_promoted'] as bool? ?? false,
        promotionState: json['promotion_state'] == null
            ? null
            : ListingPromotionState.fromJson(
                json['promotion_state'] as Map<String, dynamic>,
              ),
        description: json['description'] as String,
        addressText: json['address_text'] as String,
        moderationNote: json['moderation_note'] as String?,
        owner: OwnerCard.fromJson(json['owner'] as Map<String, dynamic>),
        mediaItems: (json['media_items'] as List<dynamic>? ?? const [])
            .map((item) => ListingMedia.fromJson(item as Map<String, dynamic>))
            .toList(),
        attributeValues: (json['attribute_values'] as List<dynamic>? ??
                const [])
            .map((item) =>
                ListingAttributeValue.fromJson(item as Map<String, dynamic>))
            .toList(),
      );
}

class ListingPage {
  const ListingPage({required this.items, required this.meta});

  final List<ListingSummary> items;
  final PaginationMeta meta;

  factory ListingPage.fromJson(Map<String, dynamic> json) => ListingPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map(
                (item) => ListingSummary.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class PublicUserProfile {
  const PublicUserProfile({
    required this.publicId,
    required this.username,
    required this.fullName,
    required this.activeListingCount,
    required this.publishedListingCount,
    required this.createdAt,
    this.bio,
    this.profileImagePath,
    this.status,
  });

  final String publicId;
  final String username;
  final String fullName;
  final int activeListingCount;
  final int publishedListingCount;
  final DateTime createdAt;
  final String? bio;
  final String? profileImagePath;
  final String? status;

  factory PublicUserProfile.fromJson(Map<String, dynamic> json) =>
      PublicUserProfile(
        publicId: json['public_id'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        activeListingCount: parseInt(json['active_listing_count']) ?? 0,
        publishedListingCount: parseInt(json['published_listing_count']) ?? 0,
        createdAt: DateTime.parse(json['created_at'] as String),
        bio: json['bio'] as String?,
        profileImagePath: json['profile_image_path'] as String?,
        status: json['status'] as String?,
      );
}

class FavoriteItem {
  const FavoriteItem({
    required this.isAvailable,
    required this.createdAt,
    this.listingPublicId,
    this.listing,
    this.unavailableReason,
  });

  final bool isAvailable;
  final DateTime createdAt;
  final String? listingPublicId;
  final ListingSummary? listing;
  final String? unavailableReason;

  factory FavoriteItem.fromJson(Map<String, dynamic> json) => FavoriteItem(
        isAvailable: json['is_available'] as bool? ?? false,
        createdAt: DateTime.parse(json['created_at'] as String),
        listingPublicId: json['listing_public_id'] as String?,
        listing: json['listing'] == null
            ? null
            : ListingSummary.fromJson(json['listing'] as Map<String, dynamic>),
        unavailableReason: json['unavailable_reason'] as String?,
      );
}

class FavoritesPage {
  const FavoritesPage({required this.items, required this.meta});

  final List<FavoriteItem> items;
  final PaginationMeta meta;

  factory FavoritesPage.fromJson(Map<String, dynamic> json) => FavoritesPage(
        items: (json['items'] as List<dynamic>? ?? const [])
            .map((item) => FavoriteItem.fromJson(item as Map<String, dynamic>))
            .toList(),
        meta: PaginationMeta.fromJson(json['meta'] as Map<String, dynamic>),
      );
}

class OwnerListing {
  const OwnerListing({
    required this.publicId,
    required this.title,
    required this.status,
    required this.priceAmount,
    required this.currencyCode,
    required this.city,
  });

  final String publicId;
  final String title;
  final String status;
  final String priceAmount;
  final String currencyCode;
  final String city;

  factory OwnerListing.fromJson(Map<String, dynamic> json) => OwnerListing(
        publicId: json['public_id'] as String,
        title: json['title'] as String,
        status: json['status'] as String,
        priceAmount: (parseDouble(json['price_amount']) ?? 0).toString(),
        currencyCode: json['currency_code'] as String,
        city: json['city'] as String,
      );
}
