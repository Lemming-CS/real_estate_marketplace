import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _usernameController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _passwordController = TextEditingController();
  String _locale = 'en';

  @override
  void dispose() {
    _emailController.dispose();
    _usernameController.dispose();
    _fullNameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    return Scaffold(
      appBar:
          AppBar(title: Text(context.tr('Create account', 'Создать аккаунт'))),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              TextFormField(
                controller: _fullNameController,
                decoration: InputDecoration(
                    labelText: context.tr('Full name', 'Полное имя')),
                validator: (value) => value == null || value.trim().length < 2
                    ? context.tr('Enter your name.', 'Введите имя.')
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _usernameController,
                decoration: InputDecoration(
                    labelText: context.tr('Username', 'Имя пользователя')),
                validator: (value) => value == null || value.trim().length < 3
                    ? context.tr('At least 3 characters.', 'Минимум 3 символа.')
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration:
                    InputDecoration(labelText: context.tr('Email', 'Email')),
                validator: (value) => value == null || value.trim().isEmpty
                    ? context.tr('Enter your email.', 'Введите email.')
                    : null,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _passwordController,
                obscureText: true,
                decoration: InputDecoration(
                    labelText: context.tr('Password', 'Пароль')),
                validator: (value) => value == null || value.length < 8
                    ? context.tr(
                        'At least 8 characters.', 'Минимум 8 символов.')
                    : null,
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                initialValue: _locale,
                decoration:
                    InputDecoration(labelText: context.tr('Language', 'Язык')),
                items: const [
                  DropdownMenuItem(value: 'en', child: Text('English')),
                  DropdownMenuItem(value: 'ru', child: Text('Русский')),
                ],
                onChanged: (value) => setState(() => _locale = value ?? 'en'),
              ),
              const SizedBox(height: 16),
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
                        final success = await ref
                            .read(authControllerProvider.notifier)
                            .register(
                              email: _emailController.text,
                              username: _usernameController.text,
                              fullName: _fullNameController.text,
                              password: _passwordController.text,
                              locale: _locale,
                            );
                        final session =
                            ref.read(authControllerProvider).session;
                        if (!context.mounted || !success || session == null) {
                          return;
                        }
                        await ref
                            .read(appLocaleControllerProvider.notifier)
                            .setLocale(session.user.locale);
                        if (!context.mounted) {
                          return;
                        }
                        context.go('/');
                      },
                child: Text(authState.isLoading
                    ? context.tr('Creating...', 'Создаем...')
                    : context.tr('Create account', 'Создать аккаунт')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
