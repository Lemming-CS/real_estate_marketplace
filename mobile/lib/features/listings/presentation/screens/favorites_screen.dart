import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/auth_required_view.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_card.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/marketplace_shell_scaffold.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class FavoritesScreen extends ConsumerWidget {
  const FavoritesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    if (!authState.isAuthenticated) {
      return MarketplaceShellScaffold(
        currentIndex: 1,
        title: context.tr('Favorites', 'Избранное'),
        body: const AuthRequiredView(),
      );
    }

    final favoritesAsync = ref.watch(favoritesProvider);
    return MarketplaceShellScaffold(
      currentIndex: 1,
      title: context.tr('Favorites', 'Избранное'),
      body: favoritesAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
                child: Text(
                    context.tr('No favorites yet.', 'Пока нет избранного.')));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: ListTile(
                  leading: const Icon(Icons.favorite),
                  title: Text(
                      context.tr('Saved favorites', 'Сохраненные избранные')),
                  trailing: Text('${page.meta.totalItems}'),
                ),
              ),
              const SizedBox(height: 12),
              ...page.items.map((item) {
                if (!item.isAvailable || item.listing == null) {
                  return Card(
                    child: ListTile(
                      title: Text(context.tr(
                          'Unavailable listing', 'Объявление недоступно')),
                      subtitle: Text(item.unavailableReason ??
                          context.tr('This listing is no longer public.',
                              'Это объявление больше не публично.')),
                    ),
                  );
                }
                return ListingCard(
                  listing: item.listing!,
                  onTap: () =>
                      context.push('/listing/${item.listing!.publicId}'),
                  trailing: IconButton(
                    onPressed: () async {
                      final token = authState.session!.accessToken;
                      final repository = ref.read(listingsRepositoryProvider);
                      await repository.toggleFavorite(
                        accessToken: token,
                        listingId: item.listing!.publicId,
                        shouldFavorite: false,
                      );
                      if (!context.mounted) {
                        return;
                      }
                      ref.invalidate(favoritesProvider);
                    },
                    icon: const Icon(Icons.favorite, color: Colors.red),
                  ),
                );
              }),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }
}
