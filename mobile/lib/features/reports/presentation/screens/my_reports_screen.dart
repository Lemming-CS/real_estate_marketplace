import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/reports/presentation/controllers/report_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class MyReportsScreen extends ConsumerWidget {
  const MyReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final reportsAsync = ref.watch(myReportsProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('My reports', 'Мои жалобы')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: reportsAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
              child: Text(
                context.tr(
                  'You have not submitted any reports yet.',
                  'Вы еще не отправляли жалобы.',
                ),
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: page.items.length,
            itemBuilder: (context, index) {
              final report = page.items[index];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(report.listingTitle ??
                      report.reportedUsername ??
                      report.reasonCode),
                  subtitle: Text(
                    [
                      report.reasonCode,
                      if ((report.description ?? '').isNotEmpty)
                        report.description!,
                      if ((report.resolutionNote ?? '').isNotEmpty)
                        '${context.tr('Resolution', 'Решение')}: ${report.resolutionNote}',
                      DateFormat('MMM d, HH:mm')
                          .format(report.createdAt.toLocal()),
                    ].join('\n'),
                  ),
                  isThreeLine: true,
                  trailing: Chip(label: Text(report.status)),
                  onTap: report.listingPublicId == null
                      ? null
                      : () =>
                          context.push('/listing/${report.listingPublicId}'),
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text(error.toString())),
      ),
    );
  }
}
