import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() =>
      _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    return Scaffold(
      appBar:
          AppBar(title: Text(context.tr('Forgot password', 'Забыли пароль'))),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: ListView(
            children: [
              Text(
                context.tr(
                  'The backend uses a mock-friendly reset flow. Submit your email to generate reset instructions.',
                  'Бэкенд использует удобный для разработки сценарий сброса. Отправьте email, чтобы получить инструкции.',
                ),
              ),
              const SizedBox(height: 20),
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
              if (authState.error != null) ...[
                Text(authState.error!,
                    style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 12),
              ],
              if (authState.resetMessage != null) ...[
                Text(authState.resetMessage!,
                    style: const TextStyle(color: Colors.green)),
                const SizedBox(height: 12),
              ],
              FilledButton(
                onPressed: authState.isLoading
                    ? null
                    : () async {
                        if (_formKey.currentState!.validate()) {
                          await ref
                              .read(authControllerProvider.notifier)
                              .forgotPassword(_emailController.text);
                        }
                      },
                child: Text(authState.isLoading
                    ? context.tr('Submitting...', 'Отправляем...')
                    : context.tr(
                        'Send reset instructions', 'Отправить инструкции')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
