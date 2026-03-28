class ListingFilters {
  const ListingFilters({
    this.query = '',
    this.purpose,
    this.propertyType,
    this.city = '',
    this.minPrice = '',
    this.maxPrice = '',
    this.minAreaSqm = '',
    this.maxAreaSqm = '',
    this.roomCount,
    this.status,
    this.sort = 'newest',
    this.page = 1,
    this.pageSize = 20,
  });

  final String query;
  final String? purpose;
  final String? propertyType;
  final String city;
  final String minPrice;
  final String maxPrice;
  final String minAreaSqm;
  final String maxAreaSqm;
  final int? roomCount;
  final String? status;
  final String sort;
  final int page;
  final int pageSize;

  ListingFilters copyWith({
    String? query,
    String? purpose,
    String? propertyType,
    String? city,
    String? minPrice,
    String? maxPrice,
    String? minAreaSqm,
    String? maxAreaSqm,
    int? roomCount,
    String? status,
    String? sort,
    int? page,
    int? pageSize,
    bool clearPurpose = false,
    bool clearPropertyType = false,
    bool clearRoomCount = false,
    bool clearStatus = false,
  }) {
    return ListingFilters(
      query: query ?? this.query,
      purpose: clearPurpose ? null : (purpose ?? this.purpose),
      propertyType:
          clearPropertyType ? null : (propertyType ?? this.propertyType),
      city: city ?? this.city,
      minPrice: minPrice ?? this.minPrice,
      maxPrice: maxPrice ?? this.maxPrice,
      minAreaSqm: minAreaSqm ?? this.minAreaSqm,
      maxAreaSqm: maxAreaSqm ?? this.maxAreaSqm,
      roomCount: clearRoomCount ? null : (roomCount ?? this.roomCount),
      status: clearStatus ? null : (status ?? this.status),
      sort: sort ?? this.sort,
      page: page ?? this.page,
      pageSize: pageSize ?? this.pageSize,
    );
  }

  Map<String, String?> toQueryParameters() => {
        'q': query.isEmpty ? null : query,
        'purpose': purpose,
        'property_type': propertyType,
        'city': city.isEmpty ? null : city,
        'min_price': minPrice.isEmpty ? null : minPrice,
        'max_price': maxPrice.isEmpty ? null : maxPrice,
        'min_area_sqm': minAreaSqm.isEmpty ? null : minAreaSqm,
        'max_area_sqm': maxAreaSqm.isEmpty ? null : maxAreaSqm,
        'room_count': roomCount?.toString(),
        'status': status,
        'sort': sort,
        'page': page.toString(),
        'page_size': pageSize.toString(),
      };
}
