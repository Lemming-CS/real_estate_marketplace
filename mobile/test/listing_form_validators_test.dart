import 'package:electronics_marketplace_mobile/features/listings/presentation/listing_form_validators.dart';
import 'package:flutter_test/flutter_test.dart';

String _en(String english, String russian) => english;
String _ru(String english, String russian) => russian;

void main() {
  test('title validator rejects empty and too-short values', () {
    expect(
      ListingFormValidators.validateTitle('', _en),
      'Title is required.',
    );
    expect(
      ListingFormValidators.validateTitle('abc', _en),
      'Title must be at least 5 characters.',
    );
    expect(ListingFormValidators.validateTitle('Sunny apartment', _en), isNull);
  });

  test('numeric validators enforce positive values and ranges', () {
    expect(
      ListingFormValidators.validatePrice('0', _en),
      'Enter a valid price.',
    );
    expect(
      ListingFormValidators.validateLatitude('120', _en),
      'Latitude must be between -90 and 90.',
    );
    expect(
      ListingFormValidators.validateLongitude('-181', _en),
      'Longitude must be between -180 and 180.',
    );
    expect(
      ListingFormValidators.validateArea('85.5', _en),
      isNull,
    );
  });

  test('apartment total floors is required but house total floors is optional',
      () {
    expect(
      ListingFormValidators.validateTotalFloors(
        '',
        _en,
        propertyType: 'apartment',
      ),
      'Total floors are required for apartments.',
    );
    expect(
      ListingFormValidators.validateTotalFloors(
        '',
        _en,
        propertyType: 'house',
      ),
      isNull,
    );
  });

  test('validators can return Russian localized messages', () {
    expect(
      ListingFormValidators.validateCity('', _ru),
      'Город обязателен.',
    );
  });
}
