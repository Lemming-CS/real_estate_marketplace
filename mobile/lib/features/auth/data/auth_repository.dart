import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/core/network/api_endpoints.dart';
import 'package:electronics_marketplace_mobile/features/auth/domain/auth_models.dart';

class AuthRepository {
  const AuthRepository(this._client);

  final ApiClient _client;

  Future<AuthSession> login({
    required String email,
    required String password,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.authLogin,
      body: {'email': email.trim(), 'password': password},
    );
    return AuthSession.fromJson(json);
  }

  Future<AuthSession> register({
    required String email,
    required String username,
    required String fullName,
    required String password,
    required String locale,
  }) async {
    final json = await _client.postJson(
      ApiEndpoints.authRegister,
      body: {
        'email': email.trim(),
        'username': username.trim(),
        'full_name': fullName.trim(),
        'password': password,
        'locale': locale,
      },
    );
    return AuthSession.fromJson(json);
  }

  Future<String> forgotPassword(String email) async {
    final json = await _client.postJson(
      ApiEndpoints.authForgotPassword,
      body: {'email': email.trim()},
    );
    return json['message'] as String? ?? 'Reset instructions generated.';
  }

  Future<AuthUser> fetchCurrentUser(String accessToken) async {
    final json =
        await _client.getJson(ApiEndpoints.authMe, accessToken: accessToken);
    return AuthUser.fromJson(json);
  }

  Future<void> logout({
    required String accessToken,
    required String refreshToken,
  }) async {
    await _client.postJson(
      ApiEndpoints.authLogout,
      accessToken: accessToken,
      body: {'refresh_token': refreshToken},
    );
  }
}
