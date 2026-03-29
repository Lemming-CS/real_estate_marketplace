import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/features/messaging/presentation/controllers/messaging_providers.dart';
import 'package:electronics_marketplace_mobile/features/notifications/presentation/controllers/notification_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/badge_icon_button.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_card.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/marketplace_shell_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});

  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  late final TextEditingController _searchController;
  late final ScrollController _scrollController;

  @override
  void initState() {
    super.initState();
    final filters = ref.read(homeListingFiltersProvider);
    _searchController = TextEditingController(text: filters.query);
    _scrollController = ScrollController()..addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController
      ..removeListener(_onScroll)
      ..dispose();
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final listingsAsync = ref.watch(homeListingsProvider);
    final filters = ref.watch(homeListingFiltersProvider);

    final isAuthenticated = ref.watch(
      authControllerProvider.select((state) => state.isAuthenticated),
    );

    final unreadMessages = isAuthenticated
        ? (ref.watch(conversationUnreadBadgeProvider).value ?? 0)
        : 0;

    final unreadNotifications = isAuthenticated
        ? (ref.watch(notificationUnreadCountProvider).value ?? 0)
        : 0;
    return MarketplaceShellScaffold(
      currentIndex: 0,
      title: AppConfig.appName,
      actions: [
        if (isAuthenticated)
          BadgeIconButton(
            icon: Icons.chat_bubble_outline,
            count: unreadMessages,
            tooltip: context.tr('Inbox', 'Сообщения'),
            onPressed: () => context.push('/conversations'),
          ),
        if (isAuthenticated)
          BadgeIconButton(
            icon: Icons.notifications_none,
            count: unreadNotifications,
            tooltip: context.tr('Notifications', 'Уведомления'),
            onPressed: () => context.push('/notifications'),
          ),
        PopupMenuButton<String>(
          onSelected: (value) {
            if (value == 'login') {
              context.push('/login');
              return;
            }
            ref.read(homeListingFiltersProvider.notifier).state =
                filters.copyWith(sort: value);
          },
          itemBuilder: (context) => [
            PopupMenuItem(
                value: 'newest',
                child: Text(context.tr('Newest first', 'Сначала новые'))),
            PopupMenuItem(
                value: 'oldest',
                child: Text(context.tr('Oldest first', 'Сначала старые'))),
            PopupMenuItem(
                value: 'price_asc',
                child:
                    Text(context.tr('Price ascending', 'Цена по возрастанию'))),
            PopupMenuItem(
                value: 'price_desc',
                child:
                    Text(context.tr('Price descending', 'Цена по убыванию'))),
            if (!isAuthenticated)
              PopupMenuItem(
                  value: 'login', child: Text(context.tr('Sign in', 'Войти'))),
          ],
          icon: const Icon(Icons.tune),
        ),
      ],
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: _searchController,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (value) {
                    ref.read(homeListingFiltersProvider.notifier).state =
                        filters.copyWith(query: value.trim());
                  },
                  decoration: InputDecoration(
                    hintText: context.tr('Search by title or description',
                        'Поиск по названию или описанию'),
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: IconButton(
                      onPressed: () => _openFiltersSheet(context, filters),
                      icon: const Icon(Icons.filter_list),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      ChoiceChip(
                        label: Text(context.tr('All', 'Все')),
                        selected: filters.purpose == null,
                        onSelected: (_) {
                          ref.read(homeListingFiltersProvider.notifier).state =
                              filters.copyWith(clearPurpose: true);
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: Text(context.tr('Rent', 'Аренда')),
                        selected: filters.purpose == 'rent',
                        onSelected: (_) {
                          ref.read(homeListingFiltersProvider.notifier).state =
                              filters.copyWith(purpose: 'rent');
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: Text(context.tr('Sale', 'Продажа')),
                        selected: filters.purpose == 'sale',
                        onSelected: (_) {
                          ref.read(homeListingFiltersProvider.notifier).state =
                              filters.copyWith(purpose: 'sale');
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: Text(context.tr('Apartments', 'Квартиры')),
                        selected: filters.propertyType == 'apartment',
                        onSelected: (_) {
                          ref.read(homeListingFiltersProvider.notifier).state =
                              filters.copyWith(propertyType: 'apartment');
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: Text(context.tr('Houses', 'Дома')),
                        selected: filters.propertyType == 'house',
                        onSelected: (_) {
                          ref.read(homeListingFiltersProvider.notifier).state =
                              filters.copyWith(propertyType: 'house');
                        },
                      ),
                    ],
                  ),
                ),
                if (_hasActiveFilters(filters)) ...[
                  const SizedBox(height: 14),
                  Text(
                    context.tr('Active filters', 'Активные фильтры'),
                    style: theme.textTheme.labelLarge?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _buildActiveFilterChips(context, filters),
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: listingsAsync.when(
              data: (feed) {
                if (feed.items.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(context.tr(
                          'No properties match the current filters.',
                          'Нет объектов по текущим фильтрам.')),
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async {
                    await ref.read(homeListingsProvider.notifier).refreshFeed();
                  },
                  child: ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 28),
                    itemCount: feed.items.length + 2,
                    itemBuilder: (context, index) {
                      if (index == 0) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 16),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 8,
                                ),
                                decoration: BoxDecoration(
                                  color: theme.colorScheme.surface,
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(
                                    color: theme.colorScheme.outlineVariant,
                                  ),
                                ),
                                child: Text(
                                  context.tr(
                                    '${feed.meta.totalItems} properties',
                                    '${feed.meta.totalItems} объектов',
                                  ),
                                  style: theme.textTheme.labelLarge?.copyWith(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                              ),
                              const Spacer(),
                              Text(
                                _sortLabel(context, filters.sort),
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: theme.colorScheme.onSurfaceVariant,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ],
                          ),
                        );
                      }
                      if (index == feed.items.length + 1) {
                        return _HomeFeedFooter(feed: feed);
                      }
                      final listing = feed.items[index - 1];
                      return ListingCard(
                        listing: listing,
                        onTap: () =>
                            context.push('/listing/${listing.publicId}'),
                      );
                    },
                  ),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(error.toString(), textAlign: TextAlign.center),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _openFiltersSheet(
      BuildContext context, ListingFilters filters) async {
    final cityController = TextEditingController(text: filters.city);
    final minPriceController = TextEditingController(text: filters.minPrice);
    final maxPriceController = TextEditingController(text: filters.maxPrice);
    final minAreaController = TextEditingController(text: filters.minAreaSqm);
    final maxAreaController = TextEditingController(text: filters.maxAreaSqm);
    final roomsController =
        TextEditingController(text: filters.roomCount?.toString() ?? '');
    String? localPurpose = filters.purpose;
    String? localPropertyType = filters.propertyType;

    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    DropdownButtonFormField<String?>(
                      initialValue: localPurpose,
                      decoration: InputDecoration(
                          labelText: context.tr('Purpose', 'Цель')),
                      items: [
                        DropdownMenuItem<String?>(
                            value: null,
                            child: Text(context.tr('Any', 'Любая'))),
                        DropdownMenuItem<String?>(
                            value: 'rent',
                            child: Text(context.tr('Rent', 'Аренда'))),
                        DropdownMenuItem<String?>(
                            value: 'sale',
                            child: Text(context.tr('Sale', 'Продажа'))),
                      ],
                      onChanged: (value) =>
                          setModalState(() => localPurpose = value),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String?>(
                      initialValue: localPropertyType,
                      decoration: InputDecoration(
                          labelText:
                              context.tr('Property type', 'Тип объекта')),
                      items: [
                        DropdownMenuItem<String?>(
                            value: null,
                            child: Text(context.tr('Any', 'Любой'))),
                        DropdownMenuItem<String?>(
                            value: 'apartment',
                            child: Text(context.tr('Apartment', 'Квартира'))),
                        DropdownMenuItem<String?>(
                            value: 'house',
                            child: Text(context.tr('House', 'Дом'))),
                      ],
                      onChanged: (value) =>
                          setModalState(() => localPropertyType = value),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                        controller: cityController,
                        decoration: InputDecoration(
                            labelText: context.tr('City', 'Город'))),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                            child: TextField(
                                controller: minPriceController,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                    labelText: context.tr(
                                        'Min price (С)', 'Мин. цена (С)'),
                                    hintText: context.tr('KGS', 'Сом')))),
                        const SizedBox(width: 12),
                        Expanded(
                            child: TextField(
                                controller: maxPriceController,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                    labelText: context.tr(
                                        'Max price (С)', 'Макс. цена (С)'),
                                    hintText: context.tr('KGS', 'Сом')))),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        context.tr(
                          'Mixed-currency price filters use KGS for comparison.',
                          'Фильтры цены для разных валют используют сомы для сравнения.',
                        ),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Theme.of(context)
                                  .colorScheme
                                  .onSurfaceVariant,
                            ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                            child: TextField(
                                controller: minAreaController,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                    labelText: context.tr(
                                        'Min area', 'Мин. площадь')))),
                        const SizedBox(width: 12),
                        Expanded(
                            child: TextField(
                                controller: maxAreaController,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                    labelText: context.tr(
                                        'Max area', 'Макс. площадь')))),
                      ],
                    ),
                    const SizedBox(height: 12),
                    TextField(
                        controller: roomsController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                            labelText: context.tr('Rooms', 'Комнаты'))),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton(
                            onPressed: () {
                              ref
                                  .read(homeListingFiltersProvider.notifier)
                                  .state = const ListingFilters();
                              _searchController.clear();
                              Navigator.of(context).pop();
                            },
                            child: Text(context.tr('Reset', 'Сбросить')),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: FilledButton(
                            onPressed: () {
                              ref
                                  .read(homeListingFiltersProvider.notifier)
                                  .state = filters.copyWith(
                                purpose: localPurpose,
                                propertyType: localPropertyType,
                                city: cityController.text.trim(),
                                minPrice: minPriceController.text.trim(),
                                maxPrice: maxPriceController.text.trim(),
                                minAreaSqm: minAreaController.text.trim(),
                                maxAreaSqm: maxAreaController.text.trim(),
                                roomCount: roomsController.text.trim().isEmpty
                                    ? null
                                    : int.tryParse(roomsController.text.trim()),
                                clearPurpose: localPurpose == null,
                                clearPropertyType: localPropertyType == null,
                                clearRoomCount:
                                    roomsController.text.trim().isEmpty,
                              );
                              Navigator.of(context).pop();
                            },
                            child: Text(context.tr('Apply', 'Применить')),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _onScroll() {
    if (!_scrollController.hasClients) {
      return;
    }
    final position = _scrollController.position;
    if (position.pixels >= position.maxScrollExtent - 600) {
      ref.read(homeListingsProvider.notifier).loadNextPage();
    }
  }

  bool _hasActiveFilters(ListingFilters filters) {
    return filters.query.isNotEmpty ||
        filters.purpose != null ||
        filters.propertyType != null ||
        filters.city.isNotEmpty ||
        filters.minPrice.isNotEmpty ||
        filters.maxPrice.isNotEmpty ||
        filters.minAreaSqm.isNotEmpty ||
        filters.maxAreaSqm.isNotEmpty ||
        filters.roomCount != null;
  }

  List<Widget> _buildActiveFilterChips(
    BuildContext context,
    ListingFilters filters,
  ) {
    final notifier = ref.read(homeListingFiltersProvider.notifier);
    final chips = <Widget>[];

    if (filters.query.isNotEmpty) {
      chips.add(
        _FilterSummaryChip(
          label: '"${filters.query}"',
          onDeleted: () {
            notifier.state = filters.copyWith(query: '');
            _searchController.clear();
          },
        ),
      );
    }
    if (filters.purpose != null) {
      chips.add(
        _FilterSummaryChip(
          label: filters.purpose == 'rent'
              ? context.tr('Rent', 'Аренда')
              : context.tr('Sale', 'Продажа'),
          onDeleted: () =>
              notifier.state = filters.copyWith(clearPurpose: true),
        ),
      );
    }
    if (filters.propertyType != null) {
      chips.add(
        _FilterSummaryChip(
          label: filters.propertyType == 'house'
              ? context.tr('House', 'Дом')
              : context.tr('Apartment', 'Квартира'),
          onDeleted: () =>
              notifier.state = filters.copyWith(clearPropertyType: true),
        ),
      );
    }
    if (filters.city.isNotEmpty) {
      chips.add(
        _FilterSummaryChip(
          label: filters.city,
          onDeleted: () => notifier.state = filters.copyWith(city: ''),
        ),
      );
    }
    if (filters.minPrice.isNotEmpty || filters.maxPrice.isNotEmpty) {
      chips.add(
        _FilterSummaryChip(
          label: context.tr(
            '${filters.minPrice.isEmpty ? '0' : filters.minPrice}-${filters.maxPrice.isEmpty ? '∞' : filters.maxPrice} С',
            '${filters.minPrice.isEmpty ? '0' : filters.minPrice}-${filters.maxPrice.isEmpty ? '∞' : filters.maxPrice} С',
          ),
          onDeleted: () =>
              notifier.state = filters.copyWith(minPrice: '', maxPrice: ''),
        ),
      );
    }
    if (filters.minAreaSqm.isNotEmpty || filters.maxAreaSqm.isNotEmpty) {
      chips.add(
        _FilterSummaryChip(
          label:
              '${filters.minAreaSqm.isEmpty ? '0' : filters.minAreaSqm}-${filters.maxAreaSqm.isEmpty ? '∞' : filters.maxAreaSqm} m²',
          onDeleted: () =>
              notifier.state = filters.copyWith(minAreaSqm: '', maxAreaSqm: ''),
        ),
      );
    }
    if (filters.roomCount != null) {
      chips.add(
        _FilterSummaryChip(
          label: context.tr(
            '${filters.roomCount} rooms',
            '${filters.roomCount} комн.',
          ),
          onDeleted: () =>
              notifier.state = filters.copyWith(clearRoomCount: true),
        ),
      );
    }

    return chips;
  }

  String _sortLabel(BuildContext context, String sort) {
    switch (sort) {
      case 'oldest':
        return context.tr('Oldest first', 'Сначала старые');
      case 'price_asc':
        return context.tr('Price ascending', 'Цена по возрастанию');
      case 'price_desc':
        return context.tr('Price descending', 'Цена по убыванию');
      case 'newest':
      default:
        return context.tr('Newest first', 'Сначала новые');
    }
  }
}

class _FilterSummaryChip extends StatelessWidget {
  const _FilterSummaryChip({
    required this.label,
    required this.onDeleted,
  });

  final String label;
  final VoidCallback onDeleted;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.only(left: 12, right: 6, top: 6, bottom: 6),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(width: 4),
            InkWell(
              onTap: onDeleted,
              borderRadius: BorderRadius.circular(999),
              child: Padding(
                padding: const EdgeInsets.all(4),
                child: Icon(
                  Icons.close,
                  size: 16,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HomeFeedFooter extends StatelessWidget {
  const _HomeFeedFooter({
    required this.feed,
  });

  final HomeListingsState feed;

  @override
  Widget build(BuildContext context) {
    if (feed.isLoadingMore) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 20),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (feed.loadMoreError != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Center(
          child: Text(
            context.tr(
              'Could not load more listings right now.',
              'Не удалось загрузить больше объявлений.',
            ),
            style: Theme.of(context).textTheme.bodySmall,
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    if (!feed.hasMore) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 18),
        child: Center(
          child: Text(
            context.tr(
              'You have reached the end of the feed.',
              'Вы дошли до конца списка.',
            ),
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                ),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }

    return const SizedBox(height: 18);
  }
}
