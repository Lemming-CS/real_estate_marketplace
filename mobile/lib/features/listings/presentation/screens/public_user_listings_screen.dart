import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_card.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class PublicUserListingsScreen extends ConsumerWidget {
  const PublicUserListingsScreen({
    super.key,
    required this.userId,
  });

  final String userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final filters = ref.watch(publicUserListingFiltersProvider(userId));
    final listingsAsync = ref.watch(publicUserListingsProvider(userId));

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Seller listings', 'Объявления продавца')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'reset') {
                ref
                    .read(publicUserListingFiltersProvider(userId).notifier)
                    .state = const ListingFilters(pageSize: 50);
                return;
              }
              ref
                  .read(publicUserListingFiltersProvider(userId).notifier)
                  .state = filters.copyWith(sort: value);
            },
            itemBuilder: (context) => [
              PopupMenuItem(
                value: 'newest',
                child: Text(context.tr('Newest first', 'Сначала новые')),
              ),
              PopupMenuItem(
                value: 'oldest',
                child: Text(context.tr('Oldest first', 'Сначала старые')),
              ),
              PopupMenuItem(
                value: 'price_asc',
                child:
                    Text(context.tr('Price ascending', 'Цена по возрастанию')),
              ),
              PopupMenuItem(
                value: 'price_desc',
                child: Text(context.tr('Price descending', 'Цена по убыванию')),
              ),
              PopupMenuItem(
                value: 'reset',
                child: Text(context.tr('Reset filters', 'Сбросить фильтры')),
              ),
            ],
          ),
        ],
      ),
      body: listingsAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    context.tr(
                      'This seller has no public listings for the current filters.',
                      'У этого продавца нет публичных объявлений по текущим фильтрам.',
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: () {
                      ref
                          .read(
                              publicUserListingFiltersProvider(userId).notifier)
                          .state = const ListingFilters(pageSize: 50);
                    },
                    child:
                        Text(context.tr('Clear filters', 'Очистить фильтры')),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: page.items.length + 1,
            itemBuilder: (context, index) {
              if (index == 0) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            context.tr(
                              'Only active public listings are shown here.',
                              'Здесь показываются только активные публичные объявления.',
                            ),
                          ),
                          const SizedBox(height: 12),
                          SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: [
                                ChoiceChip(
                                  label: Text(context.tr('All', 'Все')),
                                  selected: filters.purpose == null &&
                                      filters.propertyType == null,
                                  onSelected: (_) {
                                    ref
                                        .read(publicUserListingFiltersProvider(
                                                userId)
                                            .notifier)
                                        .state = filters.copyWith(
                                      clearPurpose: true,
                                      clearPropertyType: true,
                                    );
                                  },
                                ),
                                const SizedBox(width: 8),
                                ChoiceChip(
                                  label: Text(context.tr('Rent', 'Аренда')),
                                  selected: filters.purpose == 'rent',
                                  onSelected: (_) {
                                    ref
                                        .read(publicUserListingFiltersProvider(
                                                userId)
                                            .notifier)
                                        .state = filters.copyWith(
                                      purpose: 'rent',
                                    );
                                  },
                                ),
                                const SizedBox(width: 8),
                                ChoiceChip(
                                  label: Text(context.tr('Sale', 'Продажа')),
                                  selected: filters.purpose == 'sale',
                                  onSelected: (_) {
                                    ref
                                        .read(publicUserListingFiltersProvider(
                                                userId)
                                            .notifier)
                                        .state = filters.copyWith(
                                      purpose: 'sale',
                                    );
                                  },
                                ),
                                const SizedBox(width: 8),
                                ChoiceChip(
                                  label: Text(
                                      context.tr('Apartments', 'Квартиры')),
                                  selected: filters.propertyType == 'apartment',
                                  onSelected: (_) {
                                    ref
                                        .read(publicUserListingFiltersProvider(
                                                userId)
                                            .notifier)
                                        .state = filters.copyWith(
                                      propertyType: 'apartment',
                                    );
                                  },
                                ),
                                const SizedBox(width: 8),
                                ChoiceChip(
                                  label: Text(context.tr('Houses', 'Дома')),
                                  selected: filters.propertyType == 'house',
                                  onSelected: (_) {
                                    ref
                                        .read(publicUserListingFiltersProvider(
                                                userId)
                                            .notifier)
                                        .state = filters.copyWith(
                                      propertyType: 'house',
                                    );
                                  },
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              }
              final listing = page.items[index - 1];
              return ListingCard(
                listing: listing,
                onTap: () => context.push('/listing/${listing.publicId}'),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }
}
