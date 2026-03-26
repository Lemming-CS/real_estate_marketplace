import 'package:electronics_marketplace_mobile/core/config/app_config.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/summary_card.dart';
import 'package:flutter/material.dart';
import 'package:electronics_marketplace_mobile/l10n/arb/app_localizations.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConfig.appName),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(
            l10n.homeTitle,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          Text(
            l10n.homeSubtitle,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
          const SizedBox(height: 20),
          SummaryCard(
            title: l10n.apiBaseUrlLabel,
            value: ApiEndpoints.baseUrl,
          ),
          const SizedBox(height: 12),
          SummaryCard(
            title: l10n.routingLabel,
            value: l10n.routingValue,
          ),
          const SizedBox(height: 12),
          SummaryCard(
            title: l10n.scopeLabel,
            value: l10n.scopeValue,
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: () => context.go('/login'),
            child: Text(l10n.openLoginPlaceholder),
          ),
        ],
      ),
    );
  }
}

