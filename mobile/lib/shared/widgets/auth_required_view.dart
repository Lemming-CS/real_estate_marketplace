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
            const Icon(Icons.lock_outline, size: 44),
            const SizedBox(height: 12),
            Text(
              context.tr(
                  'Please sign in to continue.', 'Войдите, чтобы продолжить.'),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              alignment: WrapAlignment.center,
              children: [
                OutlinedButton.icon(
                  onPressed: context.canPop() ? () => context.pop() : null,
                  icon: const Icon(Icons.arrow_back),
                  label: Text(context.tr('Back', 'Назад')),
                ),
                OutlinedButton(
                  onPressed: () => context.go('/'),
                  child: Text(
                    context.tr(
                      'Continue browsing',
                      'Продолжить просмотр',
                    ),
                  ),
                ),
                FilledButton(
                  onPressed: () => context.push('/login'),
                  child: Text(context.tr('Login', 'Войти')),
                ),
                FilledButton.tonal(
                  onPressed: () => context.push('/register'),
                  child: Text(context.tr('Register', 'Регистрация')),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
