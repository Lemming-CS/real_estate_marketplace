import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
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
    final listingsAsync = ref.watch(publicUserListingsProvider(userId));
    return Scaffold(
      appBar: AppBar(
          title: Text(context.tr('Seller listings', 'Объявления продавца'))),
      body: listingsAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
                child: Text(context.tr('No active listings found.',
                    'Активных объявлений не найдено.')));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: page.items.length,
            itemBuilder: (context, index) {
              final listing = page.items[index];
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
