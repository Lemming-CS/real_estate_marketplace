import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/commerce/presentation/controllers/commerce_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class CommerceHistoryScreen extends ConsumerWidget {
  const CommerceHistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final paymentsAsync = ref.watch(paymentsProvider);
    final promotionsAsync = ref.watch(promotionsProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(
              context.tr('Payments & promotions', 'Платежи и продвижение')),
          actions: [
            IconButton(
              onPressed: () => context.go('/'),
              icon: const Icon(Icons.home_outlined),
              tooltip: context.tr('Home', 'Главная'),
            ),
          ],
          bottom: TabBar(
            tabs: [
              Tab(text: context.tr('Payments', 'Платежи')),
              Tab(text: context.tr('Promotions', 'Продвижение')),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            paymentsAsync.when(
              data: (page) {
                if (page.items.isEmpty) {
                  return Center(
                    child: Text(
                      context.tr(
                          'No payment history yet.', 'Пока нет платежей.'),
                    ),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: page.items.length,
                  itemBuilder: (context, index) {
                    final payment = page.items[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(
                          payment.listingTitle ??
                              context.tr(
                                  'Promotion payment', 'Платеж за продвижение'),
                        ),
                        subtitle: Text(
                          '${payment.amount} ${payment.currencyCode}\n${DateFormat('MMM d, HH:mm').format(payment.createdAt.toLocal())}',
                        ),
                        isThreeLine: true,
                        trailing: _StatusChip(label: payment.status),
                      ),
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(child: Text(error.toString())),
            ),
            promotionsAsync.when(
              data: (page) {
                if (page.items.isEmpty) {
                  return Center(
                    child: Text(
                      context.tr(
                        'No promotions yet. Promote one of your listings to appear higher in the feed.',
                        'Пока нет продвижений. Продвиньте одно из своих объявлений, чтобы поднять его выше в выдаче.',
                      ),
                    ),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: page.items.length,
                  itemBuilder: (context, index) {
                    final promotion = page.items[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(promotion.listingTitle),
                        subtitle: Text(
                          [
                            promotion.packageName,
                            if (promotion.targetCity != null)
                              '${context.tr('City', 'Город')}: ${promotion.targetCity}',
                            if (promotion.targetCategoryName != null)
                              '${context.tr('Category', 'Категория')}: ${promotion.targetCategoryName}',
                            DateFormat('MMM d, HH:mm')
                                .format(promotion.createdAt.toLocal()),
                          ].join('\n'),
                        ),
                        isThreeLine: true,
                        trailing: _StatusChip(label: promotion.status),
                        onTap: () => context
                            .push('/listing/${promotion.listingPublicId}'),
                      ),
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(child: Text(error.toString())),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Chip(label: Text(label));
  }
}
