import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
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

  @override
  void initState() {
    super.initState();
    final filters = ref.read(homeListingFiltersProvider);
    _searchController = TextEditingController(text: filters.query);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final listingsAsync = ref.watch(homeListingsProvider);
    final filters = ref.watch(homeListingFiltersProvider);
    final authState = ref.watch(authControllerProvider);

    return MarketplaceShellScaffold(
      currentIndex: 0,
      title: AppConfig.appName,
      actions: [
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
            if (!authState.isAuthenticated)
              PopupMenuItem(
                  value: 'login', child: Text(context.tr('Sign in', 'Войти'))),
          ],
          icon: const Icon(Icons.tune),
        ),
      ],
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Column(
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
                const SizedBox(height: 12),
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
              ],
            ),
          ),
          Expanded(
            child: listingsAsync.when(
              data: (page) {
                if (page.items.isEmpty) {
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
                    ref.invalidate(homeListingsProvider);
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
                    itemCount: page.items.length,
                    itemBuilder: (context, index) {
                      final listing = page.items[index];
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
                                    labelText:
                                        context.tr('Min price', 'Мин. цена')))),
                        const SizedBox(width: 12),
                        Expanded(
                            child: TextField(
                                controller: maxPriceController,
                                keyboardType: TextInputType.number,
                                decoration: InputDecoration(
                                    labelText: context.tr(
                                        'Max price', 'Макс. цена')))),
                      ],
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
}
