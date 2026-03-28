import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Sign in', 'Вход')),
        leading: IconButton(
          onPressed: () {
            if (context.canPop()) {
              context.pop();
              return;
            }
            context.go('/');
          },
          icon: const Icon(Icons.arrow_back),
          tooltip: context.tr('Back', 'Назад'),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: ListView(
            children: <Widget>[
              Text(
                context.tr(
                  'Access your property marketplace account.',
                  'Войдите в аккаунт маркетплейса недвижимости.',
                ),
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 24),
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration:
                    InputDecoration(labelText: context.tr('Email', 'Email')),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return context.tr('Enter your email.', 'Введите email.');
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                    labelText: context.tr('Password', 'Пароль')),
                validator: (value) {
                  if (value == null || value.length < 8) {
                    return context.tr('Password must be at least 8 characters.',
                        'Пароль должен быть не короче 8 символов.');
                  }
                  return null;
                },
              ),
              const SizedBox(height: 12),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: () => context.push('/forgot-password'),
                  child: Text(context.tr('Forgot password?', 'Забыли пароль?')),
                ),
              ),
              if (authState.error != null) ...[
                Text(authState.error!,
                    style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
              ],
              FilledButton(
                onPressed: authState.isLoading
                    ? null
                    : () async {
                        if (!_formKey.currentState!.validate()) {
                          return;
                        }
                        final authController =
                            ref.read(authControllerProvider.notifier);
                        final localeController =
                            ref.read(appLocaleControllerProvider.notifier);
                        final success = await authController.login(
                          _emailController.text,
                          _passwordController.text,
                        );
                        if (!context.mounted || !success) {
                          return;
                        }
                        final session =
                            ref.read(authControllerProvider).session;
                        if (session == null) {
                          return;
                        }
                        await localeController.setLocale(session.user.locale);
                        if (!context.mounted) {
                          return;
                        }
                        context.go('/');
                      },
                child: Text(authState.isLoading
                    ? context.tr('Signing in...', 'Входим...')
                    : context.tr('Sign in', 'Войти')),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.push('/register'),
                child: Text(context.tr('Create account', 'Создать аккаунт')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
