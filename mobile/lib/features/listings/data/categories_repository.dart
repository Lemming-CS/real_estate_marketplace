import 'package:electronics_marketplace_mobile/app/providers.dart';
import 'package:electronics_marketplace_mobile/core/network/api_client.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/category_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final categoriesRepositoryProvider = Provider<CategoriesRepository>((ref) {
  return CategoriesRepository(ref.watch(apiClientProvider));
});

class CategoriesRepository {
  const CategoriesRepository(this._client);

  final ApiClient _client;

  Future<List<CategoryOption>> getCategories(String locale) async {
    final json = await _client.getJsonList(
      '/categories',
      query: {'locale': locale},
    );
    return json
        .map((item) => CategoryOption.fromJson(item as Map<String, dynamic>))
        .expand((item) => item.flatten())
        .toList();
  }
}
