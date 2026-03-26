import 'package:electronics_marketplace_mobile/app/router/app_router.dart';
import 'package:electronics_marketplace_mobile/app/theme/app_theme.dart';
import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:flutter/material.dart';
import 'package:electronics_marketplace_mobile/l10n/arb/app_localizations.dart';

class MarketplaceApp extends StatelessWidget {
  const MarketplaceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: AppRouter.router,
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
    );
  }
}

