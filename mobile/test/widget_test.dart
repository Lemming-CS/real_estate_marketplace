import 'package:electronics_marketplace_mobile/app/app.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  testWidgets('renders starter home screen', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        child: MarketplaceApp(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Starter Home'), findsOneWidget);
  });
}

