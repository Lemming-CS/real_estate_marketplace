class AuthUser {
  const AuthUser({
    required this.publicId,
    required this.email,
    required this.username,
    required this.fullName,
    required this.locale,
    required this.status,
    required this.roles,
    this.profileImagePath,
  });

  final String publicId;
  final String email;
  final String username;
  final String fullName;
  final String locale;
  final String status;
  final List<String> roles;
  final String? profileImagePath;

  factory AuthUser.fromJson(Map<String, dynamic> json) => AuthUser(
        publicId: json['public_id'] as String,
        email: json['email'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        locale: json['locale'] as String? ?? 'en',
        status: json['status'] as String,
        roles: (json['roles'] as List<dynamic>? ?? const []).cast<String>(),
        profileImagePath: json['profile_image_path'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'public_id': publicId,
        'email': email,
        'username': username,
        'full_name': fullName,
        'locale': locale,
        'status': status,
        'roles': roles,
        'profile_image_path': profileImagePath,
      };
}

class AuthSession {
  const AuthSession({
    required this.accessToken,
    required this.refreshToken,
    required this.user,
  });

  final String accessToken;
  final String refreshToken;
  final AuthUser user;

  factory AuthSession.fromJson(Map<String, dynamic> json) => AuthSession(
        accessToken: json['access_token'] as String,
        refreshToken: json['refresh_token'] as String,
        user: AuthUser.fromJson(json['user'] as Map<String, dynamic>),
      );

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'user': user.toJson(),
      };
}

class ForgotPasswordResult {
  const ForgotPasswordResult({
    required this.message,
    this.debugResetToken,
  });

  final String message;
  final String? debugResetToken;

  factory ForgotPasswordResult.fromJson(Map<String, dynamic> json) =>
      ForgotPasswordResult(
        message: json['message'] as String? ?? 'Reset instructions generated.',
        debugResetToken: json['debug_reset_token'] as String?,
      );
}
