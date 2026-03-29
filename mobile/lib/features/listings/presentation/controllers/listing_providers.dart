import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/core/storage/guest_token_storage.dart';
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

class HomeListingsState {
  const HomeListingsState({
    required this.items,
    required this.meta,
    this.isLoadingMore = false,
    this.loadMoreError,
  });

  final List<ListingSummary> items;
  final PaginationMeta meta;
  final bool isLoadingMore;
  final String? loadMoreError;

  bool get hasMore => meta.page < meta.totalPages;

  HomeListingsState copyWith({
    List<ListingSummary>? items,
    PaginationMeta? meta,
    bool? isLoadingMore,
    String? loadMoreError,
    bool clearLoadMoreError = false,
  }) {
    return HomeListingsState(
      items: items ?? this.items,
      meta: meta ?? this.meta,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      loadMoreError:
          clearLoadMoreError ? null : (loadMoreError ?? this.loadMoreError),
    );
  }

  factory HomeListingsState.fromPage(ListingPage page) {
    return HomeListingsState(
      items: page.items,
      meta: page.meta,
    );
  }
}

final homeListingsProvider =
    AutoDisposeAsyncNotifierProvider<HomeListingsController, HomeListingsState>(
        HomeListingsController.new);

class HomeListingsController
    extends AutoDisposeAsyncNotifier<HomeListingsState> {
  late String _locale;
  late ListingFilters _filters;

  @override
  Future<HomeListingsState> build() async {
    _locale = ref.watch(appLocaleControllerProvider).languageCode;
    _filters = ref.watch(homeListingFiltersProvider);
    final page = await ref.watch(listingsRepositoryProvider).getHomeFeed(
          filters: _filters.copyWith(page: 1),
          locale: _locale,
        );
    return HomeListingsState.fromPage(page);
  }

  Future<void> refreshFeed() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      final page = await ref.read(listingsRepositoryProvider).getHomeFeed(
            filters: _filters.copyWith(page: 1),
            locale: _locale,
          );
      return HomeListingsState.fromPage(page);
    });
  }

  Future<void> loadNextPage() async {
    final current = state.valueOrNull;
    if (current == null ||
        state.isLoading ||
        current.isLoadingMore ||
        !current.hasMore) {
      return;
    }

    state = AsyncData(
      current.copyWith(
        isLoadingMore: true,
        clearLoadMoreError: true,
      ),
    );

    final nextPageNumber = current.meta.page + 1;
    try {
      final nextPage = await ref.read(listingsRepositoryProvider).getHomeFeed(
            filters: _filters.copyWith(page: nextPageNumber),
            locale: _locale,
          );
      state = AsyncData(
        HomeListingsState(
          items: _mergeUniqueListings(current.items, nextPage.items),
          meta: nextPage.meta,
        ),
      );
    } catch (error) {
      state = AsyncValue.data(
        current.copyWith(
          isLoadingMore: false,
          loadMoreError: error.toString(),
        ),
      );
    }
  }

  List<ListingSummary> _mergeUniqueListings(
    List<ListingSummary> currentItems,
    List<ListingSummary> nextItems,
  ) {
    final merged = <ListingSummary>[...currentItems];
    final seen = currentItems.map((item) => item.publicId).toSet();
    for (final item in nextItems) {
      if (seen.add(item.publicId)) {
        merged.add(item);
      }
    }
    return merged;
  }
}

final listingDetailProvider = FutureProvider.autoDispose
    .family<ListingDetail, String>((ref, listingId) async {
  final locale = ref.watch(appLocaleControllerProvider).languageCode;
  final token = ref.watch(authControllerProvider).session?.accessToken;
  final guestToken =
      token == null ? await ref.watch(guestTokenProvider.future) : null;
  return ref.watch(listingsRepositoryProvider).getListingDetail(
        listingId: listingId,
        locale: locale,
        accessToken: token,
        guestToken: guestToken,
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
