import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _requestFormKey = GlobalKey<FormState>();
  final _resetFormKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _tokenController = TextEditingController();
  final _newPasswordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _tokenController.dispose();
    _newPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: Text(context.tr('Forgot password', 'Забыли пароль')),
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
        child: ListView(
          children: [
            Text(
              context.tr(
                'The backend uses a mock-friendly reset flow. Request a token first, then submit the token with your new password.',
                'Бэкенд использует удобный для разработки сценарий сброса. Сначала запросите токен, затем отправьте токен с новым паролем.',
              ),
            ),
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _requestFormKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        context.tr(
                          '1. Request reset token',
                          '1. Запросить токен сброса',
                        ),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: InputDecoration(
                          labelText: context.tr('Email', 'Email'),
                        ),
                        validator: (value) => value == null ||
                                value.trim().isEmpty
                            ? context.tr('Enter your email.', 'Введите email.')
                            : null,
                      ),
                      const SizedBox(height: 16),
                      FilledButton(
                        onPressed: authState.isLoading
                            ? null
                            : () async {
                                if (!_requestFormKey.currentState!.validate()) {
                                  return;
                                }
                                final controller =
                                    ref.read(authControllerProvider.notifier);
                                await controller.forgotPassword(
                                  _emailController.text,
                                );
                                if (!mounted) {
                                  return;
                                }
                                final resetToken = ref
                                    .read(authControllerProvider)
                                    .debugResetToken;
                                if (resetToken != null &&
                                    _tokenController.text.trim().isEmpty) {
                                  _tokenController.text = resetToken;
                                }
                              },
                        child: Text(authState.isLoading
                            ? context.tr('Submitting...', 'Отправляем...')
                            : context.tr(
                                'Send reset instructions',
                                'Отправить инструкции',
                              )),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 16),
            if (authState.error != null) ...[
              Text(authState.error!, style: const TextStyle(color: Colors.red)),
              const SizedBox(height: 12),
            ],
            if (authState.resetMessage != null) ...[
              Text(
                authState.resetMessage!,
                style: const TextStyle(color: Colors.green),
              ),
              const SizedBox(height: 12),
            ],
            if (authState.debugResetToken != null) ...[
              Card(
                color: Theme.of(context).colorScheme.secondaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        context.tr(
                          'Debug reset token',
                          'Отладочный токен сброса',
                        ),
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      SelectableText(authState.debugResetToken!),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _resetFormKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        context.tr(
                          '2. Reset password',
                          '2. Сбросить пароль',
                        ),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _tokenController,
                        decoration: InputDecoration(
                          labelText: context.tr('Reset token', 'Токен сброса'),
                        ),
                        validator: (value) =>
                            value == null || value.trim().length < 16
                                ? context.tr(
                                    'Enter a valid reset token.',
                                    'Введите корректный токен сброса.',
                                  )
                                : null,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _newPasswordController,
                        obscureText: true,
                        decoration: InputDecoration(
                          labelText: context.tr('New password', 'Новый пароль'),
                          helperText: context.tr(
                            'Minimum 8 characters.',
                            'Минимум 8 символов.',
                          ),
                        ),
                        validator: (value) => value == null || value.length < 8
                            ? context.tr(
                                'Password must be at least 8 characters.',
                                'Пароль должен быть не короче 8 символов.',
                              )
                            : null,
                      ),
                      const SizedBox(height: 16),
                      FilledButton.tonal(
                        onPressed: authState.isLoading
                            ? null
                            : () async {
                                if (!_resetFormKey.currentState!.validate()) {
                                  return;
                                }
                                await ref
                                    .read(authControllerProvider.notifier)
                                    .resetPassword(
                                      token: _tokenController.text,
                                      newPassword: _newPasswordController.text,
                                    );
                              },
                        child: Text(authState.isLoading
                            ? context.tr('Resetting...', 'Сбрасываем...')
                            : context.tr(
                                'Reset password',
                                'Сбросить пароль',
                              )),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
