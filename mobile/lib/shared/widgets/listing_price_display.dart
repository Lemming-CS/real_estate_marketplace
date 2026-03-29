import 'package:electronics_marketplace_mobile/core/utils/json_parsers.dart';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

const _usdToKgsRate = 87.5;

class ListingPriceDisplay extends StatelessWidget {
  const ListingPriceDisplay({
    super.key,
    required this.priceAmount,
    required this.currencyCode,
    this.primaryStyle,
    this.secondaryStyle,
    this.crossAxisAlignment = CrossAxisAlignment.start,
  });

  final String priceAmount;
  final String currencyCode;
  final TextStyle? primaryStyle;
  final TextStyle? secondaryStyle;
  final CrossAxisAlignment crossAxisAlignment;

  @override
  Widget build(BuildContext context) {
    final amount = parseDouble(priceAmount) ?? 0;
    final normalizedCurrency = currencyCode.toUpperCase();
    final locale = Localizations.localeOf(context).languageCode;

    final primaryLabel = _formatMoney(
      amount: amount,
      currencyCode: normalizedCurrency,
      locale: locale,
    );
    final comparisonLabel = _formatComparisonMoney(
      amount: amount,
      currencyCode: normalizedCurrency,
      locale: locale,
    );

    return Column(
      crossAxisAlignment: crossAxisAlignment,
      children: [
        Text(primaryLabel, style: primaryStyle),
        const SizedBox(height: 2),
        Text(
          '≈ $comparisonLabel',
          style: secondaryStyle ??
              Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
        ),
      ],
    );
  }

  String _formatComparisonMoney({
    required double amount,
    required String currencyCode,
    required String locale,
  }) {
    if (currencyCode == 'USD') {
      return _formatMoney(
        amount: amount * _usdToKgsRate,
        currencyCode: 'KGS',
        locale: locale,
      );
    }
    return _formatMoney(
      amount: amount / _usdToKgsRate,
      currencyCode: 'USD',
      locale: locale,
    );
  }

  String _formatMoney({
    required double amount,
    required String currencyCode,
    required String locale,
  }) {
    final formatter = NumberFormat.decimalPatternDigits(
      locale: locale,
      decimalDigits: _hasFractionalPart(amount) ? 2 : 0,
    );
    final formattedAmount = formatter.format(amount);
    if (currencyCode == 'USD') {
      return '\$$formattedAmount';
    }
    return '$formattedAmount С';
  }

  bool _hasFractionalPart(double value) {
    return (value * 100).round() % 100 != 0;
  }
}
