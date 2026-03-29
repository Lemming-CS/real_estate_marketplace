import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/features/messaging/data/messaging_repository.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/controllers/messaging_providers.dart';
import 'package:electronics_marketplace_mobile/features/reports/data/reports_repository.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_price_display.dart';
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
  bool _ownerActionBusy = false;

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(listingDetailProvider(widget.listingId));
    final authState = ref.watch(authControllerProvider);
    final ownerListing = detailAsync.maybeWhen(
      data: (listing) => _isOwner(authState, listing),
      orElse: () => false,
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Property details', 'Детали объекта')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
          if (authState.isAuthenticated && !ownerListing)
            _ListingFavoriteAction(
              listingId: widget.listingId,
              accessToken: authState.session!.accessToken,
              favoriteBusy: _favoriteBusy,
              onBusyChanged: (value) {
                if (mounted) {
                  setState(() => _favoriteBusy = value);
                }
              },
            ),
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
                onImageTap: (media) =>
                    _openImageViewer(listing.mediaItems, media),
              ),
              const SizedBox(height: 16),
              Text(listing.title,
                  style: Theme.of(context).textTheme.headlineSmall),
              const SizedBox(height: 8),
              ListingPriceDisplay(
                priceAmount: listing.priceAmount,
                currencyCode: listing.currencyCode,
                primaryStyle: Theme.of(context)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w700),
                secondaryStyle: Theme.of(context)
                    .textTheme
                    .titleMedium
                    ?.copyWith(color: Theme.of(context).colorScheme.secondary),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 12,
                runSpacing: 8,
                children: [
                  _InfoChip(
                    label:
                        '${context.tr('Favorites', 'Избранное')}: ${listing.favoritesCount}',
                  ),
                  _InfoChip(
                    label:
                        '${context.tr('Views', 'Просмотры')}: ${listing.viewCount}',
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_ownerStatusMessage(authState, listing)
                  case final ownerMessage?) ...[
                Card(
                  color: Theme.of(context).colorScheme.secondaryContainer,
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Text(ownerMessage),
                  ),
                ),
                const SizedBox(height: 8),
              ],
              if (listing.isPromoted) ...[
                Align(
                  alignment: Alignment.centerLeft,
                  child: Chip(
                    avatar: const Icon(Icons.workspace_premium, size: 18),
                    label: Text(context.tr('Promoted', 'Продвигается')),
                  ),
                ),
                const SizedBox(height: 8),
              ],
              if (listing.promotionState != null) ...[
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.trending_up_outlined),
                    title: Text(context.tr(
                      'Promotion is active',
                      'Продвижение активно',
                    )),
                    subtitle: Text(
                      [
                        listing.promotionState!.packageName,
                        if ((listing.promotionState!.targetCity ?? '')
                            .isNotEmpty)
                          '${context.tr('City', 'Город')}: ${listing.promotionState!.targetCity}',
                        if ((listing.promotionState!.targetCategoryName ?? '')
                            .isNotEmpty)
                          '${context.tr('Category', 'Категория')}: ${listing.promotionState!.targetCategoryName}',
                      ].join('\n'),
                    ),
                  ),
                ),
                const SizedBox(height: 8),
              ],
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (listing.status == 'sold')
                    _InfoChip(
                      label: context.tr('Sold', 'Продано'),
                      icon: Icons.check_circle_outline,
                    ),
                  _InfoChip(
                      label: listing.purpose == 'rent'
                          ? context.tr('For rent', 'Аренда')
                          : context.tr('For sale', 'Продажа'),
                      icon: listing.purpose == 'rent'
                          ? Icons.key_outlined
                          : Icons.sell_outlined),
                  _InfoChip(
                      label: listing.propertyType == 'apartment'
                          ? context.tr('Apartment', 'Квартира')
                          : context.tr('House', 'Дом'),
                      icon: listing.propertyType == 'apartment'
                          ? Icons.apartment_outlined
                          : Icons.cottage_outlined),
                  _InfoChip(
                      label:
                          '${listing.roomCount} ${context.tr('rooms', 'комн.')}',
                      icon: Icons.bed_outlined),
                  _InfoChip(
                    label: '${listing.areaSqm} m²',
                    icon: Icons.straighten_outlined,
                  ),
                  if (listing.floor != null && listing.totalFloors != null)
                    _InfoChip(
                      label: '${listing.floor}/${listing.totalFloors}',
                      icon: Icons.layers_outlined,
                    ),
                ],
              ),
              const SizedBox(height: 16),
              Text(listing.description),
              const SizedBox(height: 16),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.place_outlined),
                  title: Text([
                    if ((listing.mapLabel ?? '').isNotEmpty) listing.mapLabel,
                    listing.district,
                    listing.city
                  ]
                      .whereType<String>()
                      .where((part) => part.isNotEmpty)
                      .join(', ')),
                  subtitle: Text(listing.addressText),
                ),
              ),
              const SizedBox(height: 12),
              Text(context.tr('Location', 'Локация'),
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              MapPreview(
                latitude: listing.latitude,
                longitude: listing.longitude,
                interactive: true,
              ),
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
              if (!_isOwner(authState, listing)) ...[
                const SizedBox(height: 16),
                Wrap(
                  spacing: 12,
                  runSpacing: 12,
                  children: [
                    FilledButton(
                      onPressed: () => _startConversation(authState, listing),
                      child: Text(
                          context.tr('Message seller', 'Написать продавцу')),
                    ),
                    OutlinedButton(
                      onPressed: () => _reportListing(authState, listing),
                      child: Text(context.tr('Report listing', 'Пожаловаться')),
                    ),
                  ],
                ),
              ],
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
                          final repository =
                              ref.read(listingsRepositoryProvider);
                          await repository.publishListing(
                            accessToken: authState.session!.accessToken,
                            listingId: listing.publicId,
                          );
                          if (!mounted) {
                            return;
                          }
                          ref.invalidate(
                              listingDetailProvider(widget.listingId));
                          ref.invalidate(myListingsProvider);
                        },
                        child: Text(context.tr('Publish', 'Опубликовать')),
                      ),
                    if (listing.status == 'published')
                      FilledButton(
                        onPressed: _ownerActionBusy
                            ? null
                            : () => _markListingSold(authState, listing),
                        child: Text(
                          context.tr('Mark as sold', 'Отметить как проданное'),
                        ),
                      ),
                    if (listing.status == 'published')
                      FilledButton.tonal(
                        onPressed: () => context
                            .push('/promote-listing/${listing.publicId}'),
                        child: Text(context.tr('Promote', 'Продвинуть')),
                      ),
                    OutlinedButton(
                      onPressed: _ownerActionBusy
                          ? null
                          : () => _deleteListing(authState, listing),
                      child: Text(context.tr('Delete', 'Удалить')),
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

  String? _ownerStatusMessage(AuthState authState, ListingDetail listing) {
    if (!_isOwner(authState, listing)) {
      return null;
    }
    switch (listing.status) {
      case 'inactive':
        return context.tr(
          'This listing is hidden from the public feed. You can edit it or publish it again.',
          'Это объявление скрыто из публичной выдачи. Вы можете отредактировать его или снова опубликовать.',
        );
      case 'archived':
        return context.tr(
          'This listing is archived and no longer visible to shoppers.',
          'Это объявление архивировано и больше не видно покупателям.',
        );
      case 'rejected':
        return [
          context.tr(
            'This listing is not publicly visible after moderation.',
            'Это объявление не видно публично после модерации.',
          ),
          if ((listing.moderationNote ?? '').isNotEmpty)
            listing.moderationNote!,
        ].join('\n');
      case 'draft':
        return context.tr(
          'This listing is still a draft. Publish it when you are ready.',
          'Это объявление пока в черновике. Опубликуйте его, когда будете готовы.',
        );
      case 'sold':
        return context.tr(
          'This listing is marked as sold and shown as closed in your account.',
          'Это объявление отмечено как проданное и отображается в вашем аккаунте как закрытое.',
        );
      default:
        return null;
    }
  }

  Future<void> _startConversation(
    AuthState authState,
    ListingDetail listing,
  ) async {
    if (!authState.isAuthenticated) {
      if (mounted) {
        context.push('/login');
      }
      return;
    }
    final messagingRepository = ref.read(messagingRepositoryProvider);
    final initialMessage = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _ConversationStartSheet(),
    );
    if (!mounted || initialMessage == null) {
      return;
    }
    try {
      final conversation = await messagingRepository.createOrReopenFromListing(
        accessToken: authState.session!.accessToken,
        listingId: listing.publicId,
        initialMessage: initialMessage,
      );
      if (!mounted) {
        return;
      }
      ref.invalidate(inboxProvider);
      context.push('/conversations/${conversation.publicId}');
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  Future<void> _reportListing(
      AuthState authState, ListingDetail listing) async {
    if (!authState.isAuthenticated) {
      if (mounted) {
        context.push('/login');
      }
      return;
    }
    final reportsRepository = ref.read(reportsRepositoryProvider);
    final draft = await showModalBottomSheet<_ListingReportDraft>(
      context: context,
      isScrollControlled: true,
      builder: (context) => const _ListingReportSheet(),
    );
    if (!mounted || draft == null) {
      return;
    }
    try {
      await reportsRepository.createListingReport(
        accessToken: authState.session!.accessToken,
        listingId: listing.publicId,
        reasonCode: draft.reasonCode,
        description: draft.description,
      );
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(context.tr('Report submitted.', 'Жалоба отправлена.')),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  Future<void> _deleteListing(
      AuthState authState, ListingDetail listing) async {
    final session = authState.session;
    if (session == null) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('Delete listing?', 'Удалить объявление?')),
        content: Text(
          context.tr(
            'This will remove the listing from the marketplace and favorites. Active promotions must be ended first.',
            'Это уберет объявление из маркетплейса и избранного. Активные продвижения нужно завершить заранее.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(context.tr('Cancel', 'Отмена')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(context.tr('Delete', 'Удалить')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }

    setState(() => _ownerActionBusy = true);
    final repository = ref.read(listingsRepositoryProvider);
    try {
      await repository.deleteListing(
        accessToken: session.accessToken,
        listingId: listing.publicId,
      );
      if (!mounted) {
        return;
      }
      ref.invalidate(myListingsProvider);
      ref.invalidate(homeListingsProvider);
      ref.invalidate(favoritesProvider);
      context.go('/my-listings');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            context.tr('Listing deleted.', 'Объявление удалено.'),
          ),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) {
        setState(() => _ownerActionBusy = false);
      }
    }
  }

  Future<void> _markListingSold(
      AuthState authState, ListingDetail listing) async {
    final session = authState.session;
    if (session == null) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('Mark as sold?', 'Отметить как проданное?')),
        content: Text(
          context.tr(
            'This property will remain in your listing history, but it will no longer be treated as active.',
            'Объект останется в истории ваших объявлений, но больше не будет считаться активным.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(context.tr('Cancel', 'Отмена')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(context.tr('Mark as sold', 'Отметить как проданное')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }

    setState(() => _ownerActionBusy = true);
    final repository = ref.read(listingsRepositoryProvider);
    try {
      await repository.markListingSold(
        accessToken: session.accessToken,
        listingId: listing.publicId,
      );
      if (!mounted) {
        return;
      }
      ref.invalidate(listingDetailProvider(widget.listingId));
      ref.invalidate(myListingsProvider);
      ref.invalidate(homeListingsProvider);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            context.tr(
              'Listing marked as sold.',
              'Объявление отмечено как проданное.',
            ),
          ),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    } finally {
      if (mounted) {
        setState(() => _ownerActionBusy = false);
      }
    }
  }

  void _openImageViewer(List<ListingMedia> items, ListingMedia selectedMedia) {
    final imageItems =
        items.where((item) => !item.isVideo).toList(growable: false);
    final initialIndex = imageItems.indexWhere(
      (item) => item.publicId == selectedMedia.publicId,
    );
    if (imageItems.isEmpty || initialIndex < 0) {
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (context) => _ListingImageViewerScreen(
          items: imageItems,
          initialIndex: initialIndex,
        ),
      ),
    );
  }
}

class _ListingFavoriteAction extends ConsumerWidget {
  const _ListingFavoriteAction({
    required this.listingId,
    required this.accessToken,
    required this.favoriteBusy,
    required this.onBusyChanged,
  });

  final String listingId;
  final String accessToken;
  final bool favoriteBusy;
  final ValueChanged<bool> onBusyChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final favoritesAsync = ref.watch(favoritesProvider);
    return favoritesAsync.maybeWhen(
          data: (page) {
            final isFavorited =
                page.items.any((item) => item.listingPublicId == listingId);
            return IconButton(
              onPressed: favoriteBusy
                  ? null
                  : () async {
                      final repository = ref.read(listingsRepositoryProvider);
                      onBusyChanged(true);
                      try {
                        await repository.toggleFavorite(
                          accessToken: accessToken,
                          listingId: listingId,
                          shouldFavorite: !isFavorited,
                        );
                        if (!context.mounted) {
                          return;
                        }
                        ref.invalidate(favoritesProvider);
                      } finally {
                        onBusyChanged(false);
                      }
                    },
              icon: Icon(
                isFavorited ? Icons.favorite : Icons.favorite_border,
                color: isFavorited ? Colors.red : null,
              ),
            );
          },
          orElse: () => const SizedBox.shrink(),
        ) ??
        const SizedBox.shrink();
  }
}

class _MediaGallery extends StatelessWidget {
  const _MediaGallery({
    required this.items,
    required this.pageIndex,
    required this.onPageChanged,
    required this.onImageTap,
  });

  final List<ListingMedia> items;
  final int pageIndex;
  final ValueChanged<int> onPageChanged;
  final ValueChanged<ListingMedia> onImageTap;

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
              return GestureDetector(
                onTap: () => onImageTap(item),
                child: Stack(
                  children: [
                    NetworkMediaImage(
                      assetKey: item.assetKey,
                      height: 240,
                      width: double.infinity,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    Positioned(
                      right: 12,
                      bottom: 12,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          color: Colors.black54,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 10,
                            vertical: 6,
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(
                                Icons.fullscreen,
                                color: Colors.white,
                                size: 18,
                              ),
                              const SizedBox(width: 6),
                              Text(
                                context.tr('Open', 'Открыть'),
                                style: const TextStyle(color: Colors.white),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
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

class _ListingImageViewerScreen extends StatefulWidget {
  const _ListingImageViewerScreen({
    required this.items,
    required this.initialIndex,
  });

  final List<ListingMedia> items;
  final int initialIndex;

  @override
  State<_ListingImageViewerScreen> createState() =>
      _ListingImageViewerScreenState();
}

class _ListingImageViewerScreenState extends State<_ListingImageViewerScreen> {
  late final PageController _pageController;
  late int _pageIndex;

  @override
  void initState() {
    super.initState();
    _pageIndex = widget.initialIndex;
    _pageController = PageController(initialPage: widget.initialIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(
          '${_pageIndex + 1}/${widget.items.length}',
          style: theme.textTheme.titleMedium?.copyWith(color: Colors.white),
        ),
      ),
      body: PageView.builder(
        controller: _pageController,
        itemCount: widget.items.length,
        onPageChanged: (index) {
          setState(() => _pageIndex = index);
        },
        itemBuilder: (context, index) {
          final item = widget.items[index];
          return InteractiveViewer(
            minScale: 1,
            maxScale: 4,
            child: Center(
              child: NetworkMediaImage(
                assetKey: item.assetKey,
                fit: BoxFit.contain,
                width: double.infinity,
                height: double.infinity,
              ),
            ),
          );
        },
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.label,
    this.icon,
  });

  final String label;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: icon == null ? null : Icon(icon, size: 18),
      label: Text(label),
    );
  }
}

class _ConversationStartSheet extends StatefulWidget {
  const _ConversationStartSheet();

  @override
  State<_ConversationStartSheet> createState() =>
      _ConversationStartSheetState();
}

class _ConversationStartSheetState extends State<_ConversationStartSheet> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                context.tr('Message seller', 'Написать продавцу'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _controller,
                minLines: 3,
                maxLines: 5,
                decoration: InputDecoration(
                  hintText: context.tr(
                    'Introduce yourself or ask about the property',
                    'Представьтесь или спросите о недвижимости',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () => Navigator.of(context).pop(_controller.text),
                  child: Text(context.tr('Open chat', 'Открыть чат')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ListingReportDraft {
  const _ListingReportDraft({
    required this.reasonCode,
    this.description,
  });

  final String reasonCode;
  final String? description;
}

class _ListingReportSheet extends StatefulWidget {
  const _ListingReportSheet();

  @override
  State<_ListingReportSheet> createState() => _ListingReportSheetState();
}

class _ListingReportSheetState extends State<_ListingReportSheet> {
  late final TextEditingController _descriptionController;
  String _selectedReason = 'inaccurate';

  @override
  void initState() {
    super.initState();
    _descriptionController = TextEditingController();
  }

  @override
  void dispose() {
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                context.tr('Report listing', 'Пожаловаться'),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _selectedReason,
                items: const [
                  DropdownMenuItem(
                      value: 'inaccurate', child: Text('Inaccurate')),
                  DropdownMenuItem(value: 'spam', child: Text('Spam')),
                  DropdownMenuItem(value: 'scam', child: Text('Scam')),
                  DropdownMenuItem(value: 'abuse', child: Text('Abuse')),
                ],
                onChanged: (value) => setState(
                  () => _selectedReason = value ?? 'inaccurate',
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _descriptionController,
                minLines: 3,
                maxLines: 5,
                decoration: InputDecoration(
                  hintText: context.tr(
                    'Add details for moderation',
                    'Добавьте детали для модерации',
                  ),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    Navigator.of(context).pop(
                      _ListingReportDraft(
                        reasonCode: _selectedReason,
                        description: _descriptionController.text,
                      ),
                    );
                  },
                  child: Text(context.tr('Submit report', 'Отправить жалобу')),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
