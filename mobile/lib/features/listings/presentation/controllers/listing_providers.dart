import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/categories_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/category_models.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final homeListingFiltersProvider =
    StateProvider<ListingFilters>((ref) => const ListingFilters());

final myListingFiltersProvider = StateProvider<ListingFilters>((ref) {
  return const ListingFilters(pageSize: 50);
});

final publicUserListingFiltersProvider =
    StateProvider.family<ListingFilters, String>((ref, userId) {
  return const ListingFilters(pageSize: 50);
});

final categoriesProvider =
    FutureProvider.autoDispose<List<CategoryOption>>((ref) async {
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  return ref.watch(categoriesRepositoryProvider).getCategories(locale);
});

final homeListingsProvider =
    FutureProvider.autoDispose<ListingPage>((ref) async {
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  final filters = ref.watch(homeListingFiltersProvider);
  return ref.watch(listingsRepositoryProvider).getHomeFeed(
        filters: filters,
        locale: locale,
      );
});

final listingDetailProvider = FutureProvider.autoDispose
    .family<ListingDetail, String>((ref, listingId) async {
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  final token = ref.watch(authControllerProvider).session?.accessToken;
  return ref.watch(listingsRepositoryProvider).getListingDetail(
        listingId: listingId,
        locale: locale,
        accessToken: token,
      );
});

final myListingsProvider = FutureProvider.autoDispose<ListingPage>((ref) async {
  final auth = ref.watch(authControllerProvider);
  final accessToken = auth.session?.accessToken;
  if (accessToken == null) {
    throw StateError('Authentication required.');
  }
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  final filters = ref.watch(myListingFiltersProvider);
  return ref.watch(listingsRepositoryProvider).getMyListings(
        accessToken: accessToken,
        filters: filters,
        locale: locale,
      );
});

final favoritesProvider =
    FutureProvider.autoDispose<FavoritesPage>((ref) async {
  final auth = ref.watch(authControllerProvider);
  final accessToken = auth.session?.accessToken;
  if (accessToken == null) {
    throw StateError('Authentication required.');
  }
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  return ref.watch(listingsRepositoryProvider).getFavorites(
        accessToken: accessToken,
        locale: locale,
      );
});

final publicUserProfileProvider = FutureProvider.autoDispose
    .family<PublicUserProfile, String>((ref, userId) async {
  return ref.watch(listingsRepositoryProvider).getPublicUser(userId);
});

final publicUserListingsProvider =
    FutureProvider.autoDispose.family<ListingPage, String>((ref, userId) async {
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  final filters = ref.watch(publicUserListingFiltersProvider(userId));
  return ref.watch(listingsRepositoryProvider).getPublicUserListings(
        userId: userId,
        filters: filters,
        locale: locale,
      );
});
