import 'package:electronics_marketplace_mobile/features/listings/domain/listing_filters.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('toQueryParameters omits empty values and includes pagination', () {
    const filters = ListingFilters(
      query: 'bishkek',
      purpose: 'rent',
      propertyType: 'apartment',
      city: '',
      minPrice: '',
      maxPrice: '90000',
      roomCount: 2,
      sort: 'price_desc',
      page: 3,
      pageSize: 20,
    );

    expect(
      filters.toQueryParameters(),
      {
        'q': 'bishkek',
        'purpose': 'rent',
        'property_type': 'apartment',
        'city': null,
        'min_price': null,
        'max_price': '90000',
        'min_area_sqm': null,
        'max_area_sqm': null,
        'room_count': '2',
        'status': null,
        'sort': 'price_desc',
        'page': '3',
        'page_size': '20',
      },
    );
  });

  test('copyWith can reset optional filters while preserving page size', () {
    const filters = ListingFilters(
      purpose: 'sale',
      propertyType: 'house',
      city: 'Bishkek',
      roomCount: 4,
      status: 'published',
      page: 2,
      pageSize: 50,
    );

    final reset = filters.copyWith(
      city: '',
      page: 1,
      clearPurpose: true,
      clearPropertyType: true,
      clearRoomCount: true,
      clearStatus: true,
    );

    expect(reset.purpose, isNull);
    expect(reset.propertyType, isNull);
    expect(reset.city, '');
    expect(reset.roomCount, isNull);
    expect(reset.status, isNull);
    expect(reset.page, 1);
    expect(reset.pageSize, 50);
  });
}
