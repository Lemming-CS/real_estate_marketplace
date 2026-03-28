import 'dart:io';

import 'package:electronics_marketplace_mobile/core/localization/app_locale_controller.dart';
import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/profile/data/profile_repository.dart';
import 'package:electronics_marketplace_mobile/features/profile/domain/profile_models.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/auth_required_view.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/marketplace_shell_scaffold.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

final currentProfileProvider =
    FutureProvider.autoDispose<EditableProfile>((ref) async {
  final authState = ref.watch(authControllerProvider);
  final token = authState.session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref.watch(profileRepositoryProvider).getProfile(token);
});

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _bioController = TextEditingController();
  final ImagePicker _picker = ImagePicker();

  bool _didPrefill = false;
  bool _isSaving = false;
  String _locale = 'en';

  @override
  void dispose() {
    _fullNameController.dispose();
    _phoneController.dispose();
    _bioController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    if (!authState.isAuthenticated) {
      return MarketplaceShellScaffold(
        currentIndex: 4,
        title: context.tr('Profile', 'Профиль'),
        body: const AuthRequiredView(),
      );
    }

    final profileAsync = ref.watch(currentProfileProvider);
    return MarketplaceShellScaffold(
      currentIndex: 4,
      title: context.tr('Profile', 'Профиль'),
      body: profileAsync.when(
        data: (profile) {
          _prefill(profile);
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Center(
                child: Column(
                  children: [
                    ClipOval(
                      child: profile.profileImagePath == null
                          ? CircleAvatar(
                              radius: 40,
                              child: Text(profile.fullName.characters.first
                                  .toUpperCase()),
                            )
                          : NetworkMediaImage(
                              assetKey: profile.profileImagePath!,
                              height: 80,
                              width: 80,
                            ),
                    ),
                    const SizedBox(height: 12),
                    FilledButton.tonal(
                      onPressed: _isSaving ? null : _pickProfileImage,
                      child: Text(context.tr('Change photo', 'Изменить фото')),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
              Card(
                child: ListTile(
                  title: Text(profile.email),
                  subtitle: Text('@${profile.username}'),
                  trailing: Text(profile.status),
                ),
              ),
              const SizedBox(height: 16),
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    TextFormField(
                      controller: _fullNameController,
                      decoration: InputDecoration(
                          labelText: context.tr('Full name', 'Полное имя')),
                      validator: (value) =>
                          value == null || value.trim().length < 2
                              ? context.tr('Enter your name.', 'Введите имя.')
                              : null,
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _phoneController,
                      decoration: InputDecoration(
                          labelText: context.tr('Phone', 'Телефон')),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _bioController,
                      minLines: 3,
                      maxLines: 5,
                      decoration: InputDecoration(
                          labelText: context.tr('Bio', 'О себе')),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: _locale,
                      decoration: InputDecoration(
                          labelText: context.tr('Language', 'Язык')),
                      items: const [
                        DropdownMenuItem(value: 'en', child: Text('English')),
                        DropdownMenuItem(value: 'ru', child: Text('Русский')),
                      ],
                      onChanged: (value) =>
                          setState(() => _locale = value ?? 'en'),
                    ),
                    const SizedBox(height: 16),
                    FilledButton(
                      onPressed: _isSaving ? null : _saveProfile,
                      child: Text(_isSaving
                          ? context.tr('Saving...', 'Сохраняем...')
                          : context.tr('Save settings', 'Сохранить')),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              OutlinedButton(
                onPressed: () async {
                  await ref.read(authControllerProvider.notifier).signOut();
                  if (mounted) {
                    ref.invalidate(currentProfileProvider);
                  }
                },
                child: Text(context.tr('Sign out', 'Выйти')),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }

  void _prefill(EditableProfile profile) {
    if (_didPrefill) {
      return;
    }
    _didPrefill = true;
    _fullNameController.text = profile.fullName;
    _phoneController.text = profile.phone ?? '';
    _bioController.text = profile.bio ?? '';
    _locale = profile.locale;
  }

  Future<void> _saveProfile() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    final authState = ref.read(authControllerProvider);
    final token = authState.session?.accessToken;
    if (token == null) {
      return;
    }

    setState(() => _isSaving = true);
    try {
      await ref.read(profileRepositoryProvider).updateProfile(
            accessToken: token,
            fullName: _fullNameController.text,
            phone: _phoneController.text,
            bio: _bioController.text,
            locale: _locale,
          );
      await ref.read(appLocaleControllerProvider.notifier).setLocale(_locale);
      ref.invalidate(currentProfileProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
              content:
                  Text(context.tr('Profile updated.', 'Профиль обновлен.'))),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _pickProfileImage() async {
    final authState = ref.read(authControllerProvider);
    final token = authState.session?.accessToken;
    if (token == null) {
      return;
    }
    final picked =
        await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (picked == null) {
      return;
    }
    setState(() => _isSaving = true);
    try {
      await ref.read(profileRepositoryProvider).uploadProfileImage(
            accessToken: token,
            image: File(picked.path),
          );
      ref.invalidate(currentProfileProvider);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }
}
