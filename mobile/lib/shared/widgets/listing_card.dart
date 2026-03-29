import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/listing_price_display.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';

class ListingCard extends StatelessWidget {
  const ListingCard({
    super.key,
    required this.listing,
    required this.onTap,
    this.trailing,
  });

  final ListingSummary listing;
  final VoidCallback onTap;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final radius = BorderRadius.circular(20);
    final promoted = listing.isPromoted;
    final locationLabel = <String>{
      if ((listing.mapLabel ?? '').trim().isNotEmpty) listing.mapLabel!.trim(),
      if (listing.city.trim().isNotEmpty) listing.city.trim(),
      if ((listing.district ?? '').trim().isNotEmpty) listing.district!.trim(),
    }.join(', ');
    final propertyTypeLabel = listing.propertyType == 'house'
        ? context.tr('House', 'Дом')
        : context.tr('Apartment', 'Квартира');

    final outerDecoration = BoxDecoration(
      color: promoted ? null : theme.colorScheme.surface,
      gradient: promoted
          ? const LinearGradient(
              colors: [Color(0xFFF6D8A9), Color(0xFFFFF3D9), Color(0xFFECC27E)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            )
          : null,
      borderRadius: radius,
      border:
          promoted ? null : Border.all(color: theme.colorScheme.outlineVariant),
      boxShadow: [
        BoxShadow(
          color: promoted ? const Color(0x24B37A2A) : const Color(0x140C1820),
          blurRadius: promoted ? 28 : 18,
          offset: const Offset(0, 12),
          spreadRadius: promoted ? 1 : 0,
        ),
      ],
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: DecoratedBox(
        decoration: outerDecoration,
        child: Padding(
          padding: EdgeInsets.all(promoted ? 1.4 : 0),
          child: Material(
            color:
                promoted ? const Color(0xFFFFFBF4) : theme.colorScheme.surface,
            borderRadius: radius,
            child: InkWell(
              borderRadius: radius,
              onTap: onTap,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(20),
                    ),
                    child: AspectRatio(
                      aspectRatio: 4 / 3,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          if (listing.primaryMedia != null)
                            NetworkMediaImage(
                              assetKey: listing.primaryMedia!.assetKey,
                              width: double.infinity,
                              height: double.infinity,
                            )
                          else
                            const DecoratedBox(
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [
                                    Color(0xFFE9E4DA),
                                    Color(0xFFD8D3C9),
                                  ],
                                  begin: Alignment.topCenter,
                                  end: Alignment.bottomCenter,
                                ),
                              ),
                              child: Center(
                                child: Icon(
                                  Icons.home_work_outlined,
                                  size: 52,
                                  color: Color(0xFF7C847F),
                                ),
                              ),
                            ),
                          const DecoratedBox(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                colors: [
                                  Color(0x18000000),
                                  Color(0x00000000),
                                  Color(0x66000000),
                                ],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomCenter,
                              ),
                            ),
                          ),
                          Positioned(
                            top: 12,
                            left: 12,
                            child: _ListingBadge(
                              icon: listing.purpose == 'rent'
                                  ? Icons.key_outlined
                                  : Icons.sell_outlined,
                              label: listing.purpose == 'rent'
                                  ? context.tr('For Rent', 'Аренда')
                                  : context.tr('For Sale', 'Продажа'),
                              backgroundColor: const Color(0xCC163B46),
                              foregroundColor: Colors.white,
                            ),
                          ),
                          Positioned(
                            left: 12,
                            right: 12,
                            bottom: 12,
                            child: Row(
                              children: [
                                Expanded(
                                  child: DecoratedBox(
                                    decoration: BoxDecoration(
                                      color: const Color(0x88111A1F),
                                      borderRadius: BorderRadius.circular(999),
                                    ),
                                    child: Padding(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 10,
                                        vertical: 7,
                                      ),
                                      child: Row(
                                        children: [
                                          const Icon(
                                            Icons.place_outlined,
                                            size: 15,
                                            color: Colors.white,
                                          ),
                                          const SizedBox(width: 6),
                                          Expanded(
                                            child: Text(
                                              locationLabel,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: theme.textTheme.bodySmall
                                                  ?.copyWith(
                                                color: Colors.white,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (listing.isPromoted)
                            Positioned(
                              top: 12,
                              right: 12,
                              child: _ListingBadge(
                                icon: Icons.workspace_premium,
                                label: context.tr('Featured', 'Премиум'),
                                backgroundColor: const Color(0xFFF4C86C),
                                foregroundColor: const Color(0xFF5A3D12),
                              ),
                            ),
                          if (listing.primaryMedia?.isVideo ?? false)
                            Positioned(
                              right: 12,
                              bottom: 12,
                              child: _ListingBadge(
                                icon: Icons.play_circle_fill_outlined,
                                label: context.tr('Video', 'Видео'),
                                backgroundColor: const Color(0xAA111111),
                                foregroundColor: Colors.white,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 18),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Expanded(
                              child: ListingPriceDisplay(
                                priceAmount: listing.priceAmount,
                                currencyCode: listing.currencyCode,
                                primaryStyle:
                                    theme.textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  height: 1.05,
                                  letterSpacing: -0.3,
                                ),
                                secondaryStyle:
                                    theme.textTheme.bodySmall?.copyWith(
                                  color: theme.colorScheme.secondary.withValues(
                                    alpha: 0.98,
                                  ),
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                            if (trailing != null) ...[
                              const SizedBox(width: 8),
                              trailing!,
                            ],
                          ],
                        ),
                        const SizedBox(height: 14),
                        Text(
                          listing.title,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: theme.textTheme.titleMedium?.copyWith(
                            height: 1.25,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.2,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            _MetaPill(
                              icon: listing.propertyType == 'house'
                                  ? Icons.cottage_outlined
                                  : Icons.apartment_outlined,
                              label: propertyTypeLabel,
                            ),
                            _MetaPill(
                              icon: Icons.bed_outlined,
                              label:
                                  '${listing.roomCount} ${context.tr('rooms', 'комн.')}',
                            ),
                            _MetaPill(
                              icon: Icons.straighten_outlined,
                              label: '${listing.areaSqm} m²',
                            ),
                            if (listing.floor != null &&
                                listing.totalFloors != null)
                              _MetaPill(
                                icon: Icons.layers_outlined,
                                label:
                                    '${listing.floor}/${listing.totalFloors}',
                              ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Wrap(
                          spacing: 10,
                          runSpacing: 8,
                          children: [
                            _CounterChip(
                              icon: Icons.favorite_border,
                              label: '${listing.favoritesCount}',
                            ),
                            _CounterChip(
                              icon: Icons.visibility_outlined,
                              label: '${listing.viewCount}',
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ListingBadge extends StatelessWidget {
  const _ListingBadge({
    required this.icon,
    required this.label,
    required this.backgroundColor,
    required this.foregroundColor,
  });

  final IconData icon;
  final String label;
  final Color backgroundColor;
  final Color foregroundColor;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 15, color: foregroundColor),
            const SizedBox(width: 6),
            Text(
              label,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: foregroundColor,
                    fontWeight: FontWeight.w700,
                  ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MetaPill extends StatelessWidget {
  const _MetaPill({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color:
            theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.56),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 15, color: theme.colorScheme.primary),
            const SizedBox(width: 6),
            Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w600,
                color: theme.colorScheme.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CounterChip extends StatelessWidget {
  const _CounterChip({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        color:
            theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.52),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(width: 6),
            Text(
              label,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
