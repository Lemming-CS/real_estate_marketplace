typedef ListingFormTranslator = String Function(String english, String russian);

class ListingFormValidators {
  const ListingFormValidators._();

  static String? validateTitle(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Title is required.', 'Заголовок обязателен.');
    }
    if (trimmed.length < 5) {
      return tr(
        'Title must be at least 5 characters.',
        'Заголовок должен быть не короче 5 символов.',
      );
    }
    return null;
  }

  static String? validateDescription(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Description is required.', 'Описание обязательно.');
    }
    if (trimmed.length < 20) {
      return tr(
        'Description must be at least 20 characters.',
        'Описание должно быть не короче 20 символов.',
      );
    }
    return null;
  }

  static String? validateCity(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('City is required.', 'Город обязателен.');
    }
    if (trimmed.length < 2) {
      return tr(
        'City must be at least 2 characters.',
        'Название города должно быть не короче 2 символов.',
      );
    }
    return null;
  }

  static String? validateAddress(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Address is required.', 'Адрес обязателен.');
    }
    if (trimmed.length < 5) {
      return tr(
        'Address must be at least 5 characters.',
        'Адрес должен быть не короче 5 символов.',
      );
    }
    return null;
  }

  static String? validatePrice(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Price is required.', 'Цена обязательна.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return tr('Enter a valid price.', 'Укажите корректную цену.');
    }
    return null;
  }

  static String? validateLatitude(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Latitude is required.', 'Нужна широта.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed < -90 || parsed > 90) {
      return tr(
        'Latitude must be between -90 and 90.',
        'Широта должна быть в диапазоне от -90 до 90.',
      );
    }
    return null;
  }

  static String? validateLongitude(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Longitude is required.', 'Нужна долгота.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed < -180 || parsed > 180) {
      return tr(
        'Longitude must be between -180 and 180.',
        'Долгота должна быть в диапазоне от -180 до 180.',
      );
    }
    return null;
  }

  static String? validateRoomCount(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr(
        'Room count is required.',
        'Количество комнат обязательно.',
      );
    }
    final parsed = int.tryParse(trimmed);
    if (parsed == null || parsed < 1) {
      return tr(
        'Enter a valid room count.',
        'Укажите корректное количество комнат.',
      );
    }
    return null;
  }

  static String? validateArea(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr('Area is required.', 'Площадь обязательна.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return tr('Enter a valid area.', 'Укажите корректную площадь.');
    }
    return null;
  }

  static String? validateBathrooms(String? value, ListingFormTranslator tr) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr(
        'Bathroom count is required.',
        'Количество санузлов обязательно.',
      );
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return tr(
        'Enter a valid bathroom count.',
        'Укажите корректное количество санузлов.',
      );
    }
    return null;
  }

  static String? validateTotalFloors(
    String? value,
    ListingFormTranslator tr, {
    required String propertyType,
  }) {
    if (propertyType != 'apartment') {
      return null;
    }
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return tr(
        'Total floors are required for apartments.',
        'Для квартир нужно указать общее количество этажей.',
      );
    }
    final parsed = int.tryParse(trimmed);
    if (parsed == null || parsed < 1) {
      return tr(
        'Enter a valid total floor count.',
        'Укажите корректное общее количество этажей.',
      );
    }
    return null;
  }
}
