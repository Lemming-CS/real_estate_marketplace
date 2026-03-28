import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class MarketplaceShellScaffold extends StatelessWidget {
  const MarketplaceShellScaffold({
    super.key,
    required this.currentIndex,
    required this.title,
    required this.body,
    this.actions,
    this.floatingActionButton,
  });

  final int currentIndex;
  final String title;
  final Widget body;
  final List<Widget>? actions;
  final Widget? floatingActionButton;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(title), actions: actions),
      body: body,
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: NavigationBar(
        selectedIndex: currentIndex,
        onDestinationSelected: (index) {
          final paths = [
            '/',
            '/favorites',
            '/my-listings',
            '/create-listing',
            '/profile'
          ];
          context.go(paths[index]);
        },
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.home_outlined),
              label: context.tr('Home', 'Главная')),
          NavigationDestination(
              icon: const Icon(Icons.favorite_border),
              label: context.tr('Favorites', 'Избранное')),
          NavigationDestination(
              icon: const Icon(Icons.apartment_outlined),
              label: context.tr('My listings', 'Мои объявления')),
          NavigationDestination(
              icon: const Icon(Icons.add_business_outlined),
              label: context.tr('Create', 'Создать')),
          NavigationDestination(
              icon: const Icon(Icons.person_outline),
              label: context.tr('Profile', 'Профиль')),
        ],
      ),
    );
  }
}
