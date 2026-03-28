class EditableProfile {
  const EditableProfile({
    required this.publicId,
    required this.email,
    required this.username,
    required this.fullName,
    required this.locale,
    required this.status,
    required this.roles,
    this.phone,
    this.bio,
    this.profileImagePath,
  });

  final String publicId;
  final String email;
  final String username;
  final String fullName;
  final String locale;
  final String status;
  final List<String> roles;
  final String? phone;
  final String? bio;
  final String? profileImagePath;

  factory EditableProfile.fromJson(Map<String, dynamic> json) =>
      EditableProfile(
        publicId: json['public_id'] as String,
        email: json['email'] as String,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        locale: json['locale'] as String? ?? 'en',
        status: json['status'] as String,
        roles: (json['roles'] as List<dynamic>? ?? const []).cast<String>(),
        phone: json['phone'] as String?,
        bio: json['bio'] as String?,
        profileImagePath: json['profile_image_path'] as String?,
      );
}
