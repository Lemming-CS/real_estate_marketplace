import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/commerce/data/commerce_repository.dart';
import 'package:electronics_marketplace_mobile/features/commerce/domain/commerce_models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final promotionPackagesProvider =
    FutureProvider.autoDispose<List<PromotionPackage>>((ref) async {
  return ref.watch(commerceRepositoryProvider).getPromotionPackages();
});

final paymentsProvider = FutureProvider.autoDispose<PaymentPage>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref.watch(commerceRepositoryProvider).getPayments(accessToken: token);
});

final promotionsProvider =
    FutureProvider.autoDispose<PromotionPage>((ref) async {
  final token = ref.watch(authControllerProvider).session?.accessToken;
  if (token == null) {
    throw StateError('Authentication required.');
  }
  return ref
      .watch(commerceRepositoryProvider)
      .getPromotions(accessToken: token);
});
