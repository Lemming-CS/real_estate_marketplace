import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_card.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class PublicUserProfileScreen extends ConsumerWidget {
  const PublicUserProfileScreen({
    super.key,
    required this.userId,
  });

  final String userId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profileAsync = ref.watch(publicUserProfileProvider(userId));
    final listingsAsync = ref.watch(publicUserListingsProvider(userId));

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Seller profile', 'Профиль продавца')),
        actions: [
          IconButton(
            onPressed: () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
        ],
      ),
      body: profileAsync.when(
        data: (profile) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(
                children: [
                  ClipOval(
                    child: profile.profileImagePath == null
                        ? CircleAvatar(
                            radius: 34,
                            child: Text(profile.fullName.characters.first
                                .toUpperCase()),
                          )
                        : NetworkMediaImage(
                            assetKey: profile.profileImagePath!,
                            height: 68,
                            width: 68,
                          ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(profile.fullName,
                            style: Theme.of(context).textTheme.titleLarge),
                        const SizedBox(height: 4),
                        Text('@${profile.username}'),
                        const SizedBox(height: 4),
                        Text(
                          context.tr(
                            '${profile.publishedListingCount} active listings',
                            '${profile.publishedListingCount} активных объявлений',
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if ((profile.bio ?? '').isNotEmpty) ...[
                const SizedBox(height: 16),
                Text(profile.bio!),
              ],
              const SizedBox(height: 20),
              FilledButton.tonal(
                onPressed: () => context.push('/seller/$userId/listings'),
                child: Text(context.tr('View all active listings',
                    'Смотреть все активные объявления')),
              ),
              const SizedBox(height: 20),
              Text(context.tr('Recent properties', 'Последние объекты'),
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 12),
              listingsAsync.when(
                data: (page) {
                  if (page.items.isEmpty) {
                    return Text(context.tr('No public listings available.',
                        'Публичных объявлений пока нет.'));
                  }
                  return Column(
                    children: page.items.take(3).map((listing) {
                      return ListingCard(
                        listing: listing,
                        onTap: () =>
                            context.push('/listing/${listing.publicId}'),
                      );
                    }).toList(),
                  );
                },
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, stackTrace) => Text(error.toString()),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }
}
