import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/map_preview.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ListingDetailScreen extends ConsumerStatefulWidget {
  const ListingDetailScreen({
    super.key,
    required this.listingId,
  });

  final String listingId;

  @override
  ConsumerState<ListingDetailScreen> createState() =>
      _ListingDetailScreenState();
}

class _ListingDetailScreenState extends ConsumerState<ListingDetailScreen> {
  int _pageIndex = 0;
  bool _favoriteBusy = false;

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(listingDetailProvider(widget.listingId));
    final authState = ref.watch(authControllerProvider);
    final favoritesAsync =
        authState.isAuthenticated ? ref.watch(favoritesProvider) : null;

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Property details', 'Детали объекта')),
        actions: [
          if (authState.isAuthenticated)
            favoritesAsync?.maybeWhen(
                  data: (page) {
                    final isFavorited = page.items.any(
                        (item) => item.listingPublicId == widget.listingId);
                    return IconButton(
                      onPressed: _favoriteBusy
                          ? null
                          : () async {
                              setState(() => _favoriteBusy = true);
                              try {
                                await ref
                                    .read(listingsRepositoryProvider)
                                    .toggleFavorite(
                                      accessToken:
                                          authState.session!.accessToken,
                                      listingId: widget.listingId,
                                      shouldFavorite: !isFavorited,
                                    );
                                ref.invalidate(favoritesProvider);
                              } finally {
                                if (mounted) {
                                  setState(() => _favoriteBusy = false);
                                }
                              }
                            },
                      icon: Icon(
                          isFavorited ? Icons.favorite : Icons.favorite_border,
                          color: isFavorited ? Colors.red : null),
                    );
                  },
                  orElse: () => const SizedBox.shrink(),
                ) ??
                const SizedBox.shrink(),
        ],
      ),
      body: detailAsync.when(
        data: (listing) => RefreshIndicator(
          onRefresh: () async =>
              ref.invalidate(listingDetailProvider(widget.listingId)),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _MediaGallery(
                items: listing.mediaItems,
                pageIndex: _pageIndex,
                onPageChanged: (index) => setState(() => _pageIndex = index),
              ),
              const SizedBox(height: 16),
              Text(listing.title,
                  style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              Text(
                '${listing.priceAmount} ${listing.currencyCode}',
                style: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _InfoChip(
                      label: listing.purpose == 'rent'
                          ? context.tr('For rent', 'Аренда')
                          : context.tr('For sale', 'Продажа')),
                  _InfoChip(
                      label: listing.propertyType == 'apartment'
                          ? context.tr('Apartment', 'Квартира')
                          : context.tr('House', 'Дом')),
                  _InfoChip(
                      label:
                          '${listing.roomCount} ${context.tr('rooms', 'комн.')}'),
                  _InfoChip(label: '${listing.areaSqm} m²'),
                  if (listing.floor != null && listing.totalFloors != null)
                    _InfoChip(label: '${listing.floor}/${listing.totalFloors}'),
                ],
              ),
              const SizedBox(height: 16),
              Text(listing.description),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.place_outlined),
                  title: Text([listing.district, listing.city]
                      .whereType<String>()
                      .where((part) => part.isNotEmpty)
                      .join(', ')),
                  subtitle: Text(listing.addressText),
                ),
              ),
              const SizedBox(height: 12),
              MapPreview(
                  latitude: listing.latitude, longitude: listing.longitude),
              const SizedBox(height: 16),
              Text(context.tr('Property details', 'Характеристики'),
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              ...listing.attributeValues.map(
                (attribute) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(attribute.displayName),
                  subtitle: Text(_attributeValueLabel(attribute)),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: ClipOval(
                    child: listing.owner.profileImagePath == null
                        ? CircleAvatar(
                            child: Text(listing.owner.fullName.characters.first
                                .toUpperCase()))
                        : NetworkMediaImage(
                            assetKey: listing.owner.profileImagePath!,
                            height: 48,
                            width: 48,
                          ),
                  ),
                  title: Text(listing.owner.fullName),
                  subtitle: Text(context.tr(
                    '${listing.owner.activeListingCount} active listings',
                    '${listing.owner.activeListingCount} активных объявлений',
                  )),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () =>
                      context.push('/seller/${listing.owner.publicId}'),
                ),
              ),
              if (_isOwner(authState, listing)) ...[
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton.tonal(
                      onPressed: () =>
                          context.push('/edit-listing/${listing.publicId}'),
                      child: Text(context.tr('Edit listing', 'Редактировать')),
                    ),
                    if (listing.status == 'draft' ||
                        listing.status == 'inactive')
                      FilledButton(
                        onPressed: () async {
                          await ref
                              .read(listingsRepositoryProvider)
                              .publishListing(
                                accessToken: authState.session!.accessToken,
                                listingId: listing.publicId,
                              );
                          ref.invalidate(
                              listingDetailProvider(widget.listingId));
                          ref.invalidate(myListingsProvider);
                        },
                        child: Text(context.tr('Publish', 'Опубликовать')),
                      ),
                  ],
                ),
              ],
            ],
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }

  bool _isOwner(AuthState authState, ListingDetail listing) {
    return authState.session?.user.publicId == listing.owner.publicId;
  }

  String _attributeValueLabel(ListingAttributeValue attribute) {
    if (attribute.numericValue != null) {
      final suffix = attribute.unit == null ? '' : ' ${attribute.unit}';
      return '${attribute.numericValue}$suffix';
    }
    if (attribute.optionValue != null) {
      return attribute.optionValue!;
    }
    if (attribute.booleanValue != null) {
      return attribute.booleanValue!
          ? context.tr('Yes', 'Да')
          : context.tr('No', 'Нет');
    }
    return attribute.textValue ?? '-';
  }
}

class _MediaGallery extends StatelessWidget {
  const _MediaGallery({
    required this.items,
    required this.pageIndex,
    required this.onPageChanged,
  });

  final List<ListingMedia> items;
  final int pageIndex;
  final ValueChanged<int> onPageChanged;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) {
      return Container(
        height: 240,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: Colors.grey.shade200,
          borderRadius: BorderRadius.circular(20),
        ),
        child: const Icon(Icons.house_outlined, size: 48),
      );
    }

    return Column(
      children: [
        SizedBox(
          height: 240,
          child: PageView.builder(
            itemCount: items.length,
            onPageChanged: onPageChanged,
            itemBuilder: (context, index) {
              final item = items[index];
              if (item.isVideo) {
                return Card(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.play_circle_outline, size: 48),
                          const SizedBox(height: 12),
                          Text(context.tr(
                              'Video tour available. Playback UI is planned next.',
                              'Видео-тур доступен. Воспроизведение добавим следующим шагом.')),
                        ],
                      ),
                    ),
                  ),
                );
              }
              return NetworkMediaImage(
                assetKey: item.assetKey,
                height: 240,
                width: double.infinity,
                borderRadius: BorderRadius.circular(20),
              );
            },
          ),
        ),
        if (items.length > 1) ...[
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(
              items.length,
              (index) => Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: pageIndex == index
                      ? Theme.of(context).colorScheme.primary
                      : Colors.grey.shade400,
                ),
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(label: Text(label));
  }
}
