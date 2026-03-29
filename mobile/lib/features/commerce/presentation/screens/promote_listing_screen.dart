import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/commerce/data/commerce_repository.dart';
import 'package:electronics_marketplace_mobile/features/commerce/domain/commerce_models.dart';
import 'package:electronics_marketplace_mobile/features/commerce/presentation/controllers/commerce_providers.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class PromoteListingScreen extends ConsumerStatefulWidget {
  const PromoteListingScreen({
    super.key,
    required this.listingId,
  });

  final String listingId;

  @override
  ConsumerState<PromoteListingScreen> createState() =>
      _PromoteListingScreenState();
}

class _PromoteListingScreenState extends ConsumerState<PromoteListingScreen> {
  final _cityController = TextEditingController();
  String? _packageId;
  String? _categoryId;
  int _durationDays = 0;
  bool _isSubmitting = false;
  String? _error;
  PromotionInitiationResult? _initiated;
  PaymentSimulationResult? _completed;

  @override
  void dispose() {
    _cityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final detailAsync = ref.watch(listingDetailProvider(widget.listingId));
    final packagesAsync = ref.watch(promotionPackagesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Promote listing', 'Продвинуть объявление')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: detailAsync.when(
        data: (listing) {
          _cityController.text = _cityController.text.isEmpty
              ? listing.city
              : _cityController.text;
          _categoryId ??= listing.category.publicId;
          return packagesAsync.when(
            data: (packages) {
              if (packages.isEmpty) {
                return Center(
                  child: Text(
                    context.tr(
                      'No active promotion packages are available right now.',
                      'Сейчас нет доступных пакетов продвижения.',
                    ),
                  ),
                );
              }

              final selectedPackage = packages.firstWhere(
                (item) => item.publicId == _packageId,
                orElse: () {
                  final fallback = packages.first;
                  _packageId = fallback.publicId;
                  _durationDays = fallback.durationDays;
                  return fallback;
                },
              );
              _durationDays = _durationDays == 0
                  ? selectedPackage.durationDays
                  : _durationDays;

              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: ListTile(
                      title: Text(listing.title),
                      subtitle: Text(
                        context.tr(
                          'Only active published listings can be promoted.',
                          'Продвигать можно только активные опубликованные объявления.',
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (_error != null) ...[
                    Card(
                      color: Theme.of(context).colorScheme.errorContainer,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Text(_error!),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  DropdownButtonFormField<String>(
                    initialValue: _packageId,
                    decoration: InputDecoration(
                      labelText: context.tr('Package', 'Пакет'),
                    ),
                    items: packages
                        .map(
                          (item) => DropdownMenuItem(
                            value: item.publicId,
                            child: Text(
                              '${item.name} • ${item.priceAmount} ${item.currencyCode}',
                            ),
                          ),
                        )
                        .toList(),
                    onChanged: _isSubmitting
                        ? null
                        : (value) {
                            final package = packages.firstWhere(
                              (item) => item.publicId == value,
                            );
                            setState(() {
                              _packageId = value;
                              _durationDays = package.durationDays;
                              _error = null;
                              _initiated = null;
                              _completed = null;
                            });
                          },
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    controller: _cityController,
                    decoration: InputDecoration(
                      labelText: context.tr('Target city', 'Целевой город'),
                      helperText: context.tr(
                        'Required for city-based promotion targeting.',
                        'Обязательно для городского таргетинга.',
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextFormField(
                    initialValue: _durationDays.toString(),
                    keyboardType: TextInputType.number,
                    decoration: InputDecoration(
                      labelText:
                          context.tr('Duration (days)', 'Длительность (дни)'),
                    ),
                    onChanged: (value) {
                      setState(() {
                        _durationDays =
                            int.tryParse(value) ?? selectedPackage.durationDays;
                      });
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: _categoryId,
                    decoration: InputDecoration(
                      labelText:
                          context.tr('Target category', 'Целевая категория'),
                    ),
                    items: [
                      DropdownMenuItem(
                        value: listing.category.publicId,
                        child: Text(listing.category.name),
                      ),
                    ],
                    onChanged: _isSubmitting
                        ? null
                        : (value) => setState(() => _categoryId = value),
                  ),
                  const SizedBox(height: 20),
                  Card(
                    child: ListTile(
                      title:
                          Text(context.tr('Price summary', 'Сводка по цене')),
                      subtitle: Text(
                        '${selectedPackage.priceAmount} ${selectedPackage.currencyCode} • ${context.tr('Base duration', 'Базовая длительность')}: ${selectedPackage.durationDays}',
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _isSubmitting ? null : _initiatePromotion,
                    child: Text(
                      _isSubmitting
                          ? context.tr('Processing...', 'Обрабатываем...')
                          : context.tr(
                              'Start mock payment', 'Начать mock-платеж'),
                    ),
                  ),
                  if (_initiated != null) ...[
                    const SizedBox(height: 20),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.tr(
                                'Pending promotion request created.',
                                'Заявка на продвижение создана.',
                              ),
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '${_initiated!.priceBreakdown.totalAmount} ${_initiated!.priceBreakdown.currencyCode}',
                            ),
                            const SizedBox(height: 12),
                            FilledButton.tonal(
                              onPressed: _isSubmitting ||
                                      _initiated!.payment.checkoutUrl == null
                                  ? null
                                  : _completeMockPayment,
                              child: Text(
                                context.tr(
                                  'Complete mock payment',
                                  'Завершить mock-платеж',
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                  if (_completed != null) ...[
                    const SizedBox(height: 20),
                    Card(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              context.tr(
                                'Promotion status updated.',
                                'Статус продвижения обновлен.',
                              ),
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '${context.tr('Payment', 'Платеж')}: ${_completed!.payment.status}\n${context.tr('Promotion', 'Продвижение')}: ${_completed!.promotion?.status ?? '-'}',
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              );
            },
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => Center(child: Text(error.toString())),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text(error.toString())),
      ),
    );
  }

  Future<void> _initiatePromotion() async {
    final authState = ref.read(authControllerProvider);
    final token = authState.session?.accessToken;
    if (token == null || _packageId == null || _categoryId == null) {
      return;
    }
    setState(() {
      _isSubmitting = true;
      _error = null;
      _completed = null;
    });
    try {
      final initiated =
          await ref.read(commerceRepositoryProvider).initiatePromotion(
                accessToken: token,
                listingId: widget.listingId,
                packageId: _packageId!,
                durationDays: _durationDays,
                targetCity: _cityController.text.trim(),
                targetCategoryPublicId: _categoryId,
              );
      if (!mounted) {
        return;
      }
      setState(() => _initiated = initiated);
      ref.invalidate(paymentsProvider);
      ref.invalidate(promotionsProvider);
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _completeMockPayment() async {
    final authState = ref.read(authControllerProvider);
    final token = authState.session?.accessToken;
    final checkoutUrl = _initiated?.payment.checkoutUrl;
    if (token == null || checkoutUrl == null) {
      return;
    }
    setState(() => _isSubmitting = true);
    try {
      final result =
          await ref.read(commerceRepositoryProvider).completeMockCheckout(
                accessToken: token,
                checkoutUrl: checkoutUrl,
              );
      if (!mounted) {
        return;
      }
      setState(() => _completed = result);
      ref.invalidate(paymentsProvider);
      ref.invalidate(promotionsProvider);
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(widget.listingId));
    } catch (error) {
      if (!mounted) {
        return;
      }
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}
