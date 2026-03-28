class CategoryOption {
  const CategoryOption({
    required this.publicId,
    required this.slug,
    required this.name,
    this.description,
    this.children = const [],
  });

  final String publicId;
  final String slug;
  final String name;
  final String? description;
  final List<CategoryOption> children;

  factory CategoryOption.fromJson(Map<String, dynamic> json) => CategoryOption(
        publicId: json['public_id'] as String,
        slug: json['slug'] as String,
        name: json['name'] as String,
        description: json['description'] as String?,
        children: (json['children'] as List<dynamic>? ?? const [])
            .map(
                (item) => CategoryOption.fromJson(item as Map<String, dynamic>))
            .toList(),
      );

  List<CategoryOption> flatten() {
    return [
      this,
      for (final child in children) ...child.flatten(),
    ];
  }
}
