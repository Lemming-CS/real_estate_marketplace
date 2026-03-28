import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/app/router/app_router.dart';
import 'package:electronics_marketplace_mobile/app/theme/app_theme.dart';
import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:flutter/material.dart';
import 'package:electronics_marketplace_mobile/l10n/arb/app_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class MarketplaceApp extends ConsumerWidget {
  const MarketplaceApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(appLocaleControllerProvider);
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
      locale: locale,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    );
  }
}
