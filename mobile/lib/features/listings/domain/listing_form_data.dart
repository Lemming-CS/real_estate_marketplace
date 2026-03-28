class ListingFormData {
  const ListingFormData({
    this.publicId,
    this.categoryPublicId = '',
    this.title = '',
    this.description = '',
    this.purpose = 'rent',
    this.propertyType = 'apartment',
    this.priceAmount = '',
    this.currencyCode = 'USD',
    this.city = '',
    this.district = '',
    this.addressText = '',
    this.mapLabel = '',
    this.latitude = '',
    this.longitude = '',
    this.roomCount = '',
    this.areaSqm = '',
    this.floor = '',
    this.totalFloors = '',
    this.furnished = false,
    this.heatingType = 'central',
    this.bathrooms = '1',
  });

  final String? publicId;
  final String categoryPublicId;
  final String title;
  final String description;
  final String purpose;
  final String propertyType;
  final String priceAmount;
  final String currencyCode;
  final String city;
  final String district;
  final String addressText;
  final String mapLabel;
  final String latitude;
  final String longitude;
  final String roomCount;
  final String areaSqm;
  final String floor;
  final String totalFloors;
  final bool furnished;
  final String heatingType;
  final String bathrooms;

  ListingFormData copyWith({
    String? publicId,
    String? categoryPublicId,
    String? title,
    String? description,
    String? purpose,
    String? propertyType,
    String? priceAmount,
    String? currencyCode,
    String? city,
    String? district,
    String? addressText,
    String? mapLabel,
    String? latitude,
    String? longitude,
    String? roomCount,
    String? areaSqm,
    String? floor,
    String? totalFloors,
    bool? furnished,
    String? heatingType,
    String? bathrooms,
  }) {
    return ListingFormData(
      publicId: publicId ?? this.publicId,
      categoryPublicId: categoryPublicId ?? this.categoryPublicId,
      title: title ?? this.title,
      description: description ?? this.description,
      purpose: purpose ?? this.purpose,
      propertyType: propertyType ?? this.propertyType,
      priceAmount: priceAmount ?? this.priceAmount,
      currencyCode: currencyCode ?? this.currencyCode,
      city: city ?? this.city,
      district: district ?? this.district,
      addressText: addressText ?? this.addressText,
      mapLabel: mapLabel ?? this.mapLabel,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      roomCount: roomCount ?? this.roomCount,
      areaSqm: areaSqm ?? this.areaSqm,
      floor: floor ?? this.floor,
      totalFloors: totalFloors ?? this.totalFloors,
      furnished: furnished ?? this.furnished,
      heatingType: heatingType ?? this.heatingType,
      bathrooms: bathrooms ?? this.bathrooms,
    );
  }
}
