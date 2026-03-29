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

class MyListingsScreen extends ConsumerWidget {
  const MyListingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authControllerProvider);
    if (!authState.isAuthenticated) {
      return MarketplaceShellScaffold(
        currentIndex: 2,
        title: context.tr('My listings', 'Мои объявления'),
        body: const AuthRequiredView(),
      );
    }

    final listingsAsync = ref.watch(myListingsProvider);
    final filters = ref.watch(myListingFiltersProvider);
    return MarketplaceShellScaffold(
      currentIndex: 2,
      title: context.tr('My listings', 'Мои объявления'),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/create-listing'),
        icon: const Icon(Icons.add),
        label: Text(context.tr('Create', 'Создать')),
      ),
      actions: [
        DropdownButton<String?>(
          value: filters.status,
          hint: Text(context.tr('Status', 'Статус')),
          underline: const SizedBox.shrink(),
          items: const [
            DropdownMenuItem<String?>(value: null, child: Text('All')),
            DropdownMenuItem(value: 'draft', child: Text('Draft')),
            DropdownMenuItem(value: 'published', child: Text('Published')),
            DropdownMenuItem(value: 'inactive', child: Text('Inactive')),
            DropdownMenuItem(value: 'archived', child: Text('Archived')),
            DropdownMenuItem(value: 'sold', child: Text('Sold')),
          ],
          onChanged: (value) {
            ref.read(myListingFiltersProvider.notifier).state =
                filters.copyWith(
              status: value,
              clearStatus: value == null,
            );
          },
        ),
      ],
      body: listingsAsync.when(
        data: (page) {
          if (page.items.isEmpty) {
            return Center(
                child: Text(context.tr('You have not created any listings yet.',
                    'Вы пока не создали объявлений.')));
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: page.items.length,
            itemBuilder: (context, index) {
              final listing = page.items[index];
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (listing.status == 'sold')
                    _OwnerStatusBanner(
                      icon: Icons.check_circle_outline,
                      title: context.tr('Sold', 'Продано'),
                      message: context.tr(
                        'This property is closed and no longer treated as active.',
                        'Этот объект закрыт и больше не считается активным.',
                      ),
                    ),
                  ListingCard(
                    listing: listing,
                    onTap: () => context.push('/listing/${listing.publicId}'),
                    trailing: _ListingActionsMenu(
                      status: listing.status,
                      isPromoted: listing.isPromoted,
                      onSelected: (action) async {
                        final token = authState.session!.accessToken;
                        final repository = ref.read(listingsRepositoryProvider);
                        switch (action) {
                          case 'edit':
                            context.push('/edit-listing/${listing.publicId}');
                            return;
                          case 'promote':
                            context
                                .push('/promote-listing/${listing.publicId}');
                            return;
                          case 'publish':
                            await repository.publishListing(
                              accessToken: token,
                              listingId: listing.publicId,
                            );
                            break;
                          case 'archive':
                            await repository.archiveListing(
                              accessToken: token,
                              listingId: listing.publicId,
                            );
                            break;
                          case 'reactivate':
                            await repository.reactivateListing(
                              accessToken: token,
                              listingId: listing.publicId,
                            );
                            break;
                          case 'mark_sold':
                            final confirmed = await _confirmMarkSold(context);
                            if (confirmed != true || !context.mounted) {
                              return;
                            }
                            await repository.markListingSold(
                              accessToken: token,
                              listingId: listing.publicId,
                            );
                            break;
                          case 'delete':
                            final confirmed = await _confirmDelete(context);
                            if (confirmed != true || !context.mounted) {
                              return;
                            }
                            await repository.deleteListing(
                              accessToken: token,
                              listingId: listing.publicId,
                            );
                            break;
                        }
                        if (!context.mounted) {
                          return;
                        }
                        ref.invalidate(myListingsProvider);
                        ref.invalidate(homeListingsProvider);
                        ref.invalidate(listingDetailProvider(listing.publicId));
                      },
                    ),
                  ),
                ],
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }

  Future<bool?> _confirmDelete(BuildContext context) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('Delete listing?', 'Удалить объявление?')),
        content: Text(
          context.tr(
            'This will remove the listing from the marketplace and favorites. This action cannot be undone from the app.',
            'Это уберет объявление из маркетплейса и избранного. Вернуть его из приложения будет нельзя.',
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
  }

  Future<bool?> _confirmMarkSold(BuildContext context) {
    return showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('Mark as sold?', 'Отметить как проданное?')),
        content: Text(
          context.tr(
            'This listing will stay in your account history, but it will no longer behave like an active property.',
            'Объявление останется в истории вашего аккаунта, но больше не будет считаться активным объектом.',
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
  }
}

class _ListingActionsMenu extends StatelessWidget {
  const _ListingActionsMenu({
    required this.status,
    required this.isPromoted,
    required this.onSelected,
  });

  final String status;
  final bool isPromoted;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        if (status == 'sold')
          Container(
            margin: const EdgeInsets.only(bottom: 6),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Theme.of(context)
                  .colorScheme
                  .secondaryContainer
                  .withValues(alpha: 0.9),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              context.tr('Sold', 'Продано'),
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
          ),
        PopupMenuButton<String>(
          onSelected: onSelected,
          itemBuilder: (context) => [
            PopupMenuItem(
              value: 'edit',
              child: Text(context.tr('Edit', 'Редактировать')),
            ),
            if (status == 'published' && !isPromoted)
              PopupMenuItem(
                value: 'promote',
                child: Text(context.tr('Promote', 'Продвинуть')),
              ),
            if (status == 'draft' || status == 'inactive')
              PopupMenuItem(
                value: 'publish',
                child: Text(context.tr('Publish', 'Опубликовать')),
              ),
            if (status == 'published')
              PopupMenuItem(
                value: 'mark_sold',
                child:
                    Text(context.tr('Mark as sold', 'Отметить как проданное')),
              ),
            if (status == 'published')
              PopupMenuItem(
                value: 'archive',
                child: Text(context.tr('Archive', 'Архивировать')),
              ),
            if (status == 'archived' || status == 'inactive')
              PopupMenuItem(
                value: 'reactivate',
                child: Text(context.tr('Reactivate', 'Активировать')),
              ),
            PopupMenuItem(
              value: 'delete',
              child: Text(context.tr('Delete', 'Удалить')),
            ),
          ],
        ),
      ],
    );
  }
}

class _OwnerStatusBanner extends StatelessWidget {
  const _OwnerStatusBanner({
    required this.icon,
    required this.title,
    required this.message,
  });

  final IconData icon;
  final String title;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer.withValues(alpha: 0.72),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: theme.colorScheme.secondary),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(message, style: theme.textTheme.bodySmall),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
