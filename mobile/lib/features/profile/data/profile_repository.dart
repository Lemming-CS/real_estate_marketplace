import 'dart:io';

import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/profile/domain/profile_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mime/mime.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(ref.watch(apiClientProvider));
});

class ProfileRepository {
  const ProfileRepository(this._client);

  final ApiClient _client;

  Future<EditableProfile> getProfile(String accessToken) async {
    final json =
        await _client.getJson(ApiEndpoints.profileMe, accessToken: accessToken);
    return EditableProfile.fromJson(json);
  }

  Future<EditableProfile> updateProfile({
    required String accessToken,
    required String fullName,
    required String phone,
    required String bio,
    required String locale,
  }) async {
    final json = await _client.patchJson(
      ApiEndpoints.profileMe,
      accessToken: accessToken,
      body: {
        'full_name': fullName,
        'phone': phone.isEmpty ? null : phone,
        'bio': bio.isEmpty ? null : bio,
        'locale': locale,
      },
    );
    return EditableProfile.fromJson(json);
  }

  Future<void> uploadProfileImage({
    required String accessToken,
    required File image,
  }) async {
    final mimeType = lookupMimeType(image.path);
    if (mimeType == null || !mimeType.startsWith('image/')) {
      throw const ApiException(
        'Selected file must be an image (jpeg, png, webp, or another image/* type).',
      );
    }

    await _client.postMultipart(
      ApiEndpoints.profileImage,
      accessToken: accessToken,
      files: [image],
      fileField: 'file',
    );
  }
}
