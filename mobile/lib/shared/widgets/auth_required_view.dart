import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AuthRequiredView extends StatelessWidget {
  const AuthRequiredView({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              context.tr(
                  'Please sign in to continue.', 'Войдите, чтобы продолжить.'),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.push('/login'),
              child: Text(context.tr('Open login', 'Открыть вход')),
            ),
          ],
        ),
      ),
    );
  }
}
