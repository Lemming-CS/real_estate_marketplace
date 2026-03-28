import 'dart:io';

import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_form_data.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final listingsRepositoryProvider = Provider<ListingsRepository>((ref) {
  return ListingsRepository(ref.watch(apiClientProvider));
});

class ListingsRepository {
  const ListingsRepository(this._client);

  final ApiClient _client;

  Future<ListingPage> getHomeFeed({
    required ListingFilters filters,
    required String locale,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.listings,
      query: {
        ...filters.toQueryParameters(),
        'locale': locale,
        'promoted_first': 'true'
      },
    );
    return ListingPage.fromJson(json);
  }

  Future<ListingPage> getMyListings({
    required String accessToken,
    required ListingFilters filters,
    required String locale,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.myListings,
      accessToken: accessToken,
      query: {...filters.toQueryParameters(), 'locale': locale},
    );
    return ListingPage.fromJson(json);
  }

  Future<ListingDetail> getListingDetail({
    required String listingId,
    required String locale,
    String? accessToken,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.listingDetail(listingId),
      accessToken: accessToken,
      query: {'locale': locale},
    );
    return ListingDetail.fromJson(json);
  }

  Future<PublicUserProfile> getPublicUser(String userId) async {
    final json = await _client.getJson(ApiEndpoints.publicUser(userId));
    return PublicUserProfile.fromJson(json);
  }

  Future<ListingPage> getPublicUserListings({
    required String userId,
    required ListingFilters filters,
    required String locale,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.publicUserListings(userId),
      query: {...filters.toQueryParameters(), 'locale': locale},
    );
    return ListingPage.fromJson(json);
  }

  Future<FavoritesPage> getFavorites({
    required String accessToken,
    required String locale,
  }) async {
    final json = await _client.getJson(
      ApiEndpoints.favorites,
      accessToken: accessToken,
      query: {'locale': locale, 'page': '1', 'page_size': '50'},
    );
    return FavoritesPage.fromJson(json);
  }

  Future<void> toggleFavorite({
    required String accessToken,
    required String listingId,
    required bool shouldFavorite,
  }) async {
    if (shouldFavorite) {
      await _client.postJson(ApiEndpoints.favorite(listingId),
          accessToken: accessToken);
      return;
    }
    await _client.deleteJson(ApiEndpoints.favorite(listingId),
        accessToken: accessToken);
  }

  Future<ListingDetail> createListing({
    required String accessToken,
    required String locale,
    required ListingFormData data,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.listings,
      accessToken: accessToken,
      query: {'locale': locale},
      body: _listingBody(data),
    );
    return ListingDetail.fromJson(json);
  }

  Future<ListingDetail> updateListing({
    required String accessToken,
    required String locale,
    required ListingFormData data,
  }) async {
    final json = await _client.patchJson(
      ApiEndpoints.listingDetail(data.publicId!),
      accessToken: accessToken,
      query: {'locale': locale},
      body: _listingBody(data),
    );
    return ListingDetail.fromJson(json);
  }

  Future<void> uploadListingImages({
    required String accessToken,
    required String listingId,
    required List<File> images,
  }) async {
    for (final file in images) {
      await _client.postMultipart(
        ApiEndpoints.listingMedia(listingId),
        accessToken: accessToken,
        files: [file],
      );
    }
  }

  Future<void> publishListing({
    required String accessToken,
    required String listingId,
  }) async {
    await _client.postJson(
      ApiEndpoints.publishListing(listingId),
      accessToken: accessToken,
    );
  }

  Future<void> archiveListing({
    required String accessToken,
    required String listingId,
  }) async {
    await _client.postJson(
      '${ApiEndpoints.listingDetail(listingId)}/archive',
      accessToken: accessToken,
    );
  }

  Future<void> reactivateListing({
    required String accessToken,
    required String listingId,
  }) async {
    await _client.postJson(
      '${ApiEndpoints.listingDetail(listingId)}/reactivate',
      accessToken: accessToken,
    );
  }

  Map<String, dynamic> _listingBody(ListingFormData data) {
    final attributeValues = <Map<String, dynamic>>[
      {'attribute_code': 'bathrooms', 'numeric_value': data.bathrooms.trim()},
    ];
    if (data.propertyType == 'apartment') {
      attributeValues.add(
          {'attribute_code': 'heating_type', 'option_value': data.heatingType});
    }

    return {
      'category_public_id': data.categoryPublicId,
      'title': data.title.trim(),
      'description': data.description.trim(),
      'purpose': data.purpose,
      'property_type': data.propertyType,
      'price_amount': data.priceAmount.trim(),
      'currency_code': data.currencyCode.trim(),
      'city': data.city.trim(),
      'district': data.district.trim().isEmpty ? null : data.district.trim(),
      'address_text': data.addressText.trim(),
      'map_label': data.mapLabel.trim().isEmpty ? null : data.mapLabel.trim(),
      'latitude': data.latitude.trim(),
      'longitude': data.longitude.trim(),
      'room_count': int.parse(data.roomCount.trim()),
      'area_sqm': data.areaSqm.trim(),
      'floor': data.floor.trim().isEmpty ? null : int.parse(data.floor.trim()),
      'total_floors': data.totalFloors.trim().isEmpty
          ? null
          : int.parse(data.totalFloors.trim()),
      'furnished': data.furnished,
      'attribute_values': attributeValues,
    };
  }
}
