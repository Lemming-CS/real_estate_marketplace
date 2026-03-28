import 'dart:io';

import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/category_models.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_form_data.dart';
import 'package:electronics_marketplace_mobile/features/listings/presentation/controllers/listing_providers.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/map_preview.dart';
import 'package:electronics_marketplace_mobile/shared/widgets/network_media_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

class ListingFormScreen extends ConsumerStatefulWidget {
  const ListingFormScreen({
    super.key,
    this.listingId,
  });

  final String? listingId;

  @override
  ConsumerState<ListingFormScreen> createState() => _ListingFormScreenState();
}

class _ListingFormScreenState extends ConsumerState<ListingFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _cityController = TextEditingController();
  final _districtController = TextEditingController();
  final _addressController = TextEditingController();
  final _mapLabelController = TextEditingController();
  final _latitudeController = TextEditingController();
  final _longitudeController = TextEditingController();
  final _roomsController = TextEditingController();
  final _areaController = TextEditingController();
  final _floorController = TextEditingController();
  final _totalFloorsController = TextEditingController();
  final _priceController = TextEditingController();
  final _bathroomsController = TextEditingController(text: '1');
  final ImagePicker _picker = ImagePicker();

  String _purpose = 'rent';
  String _propertyType = 'apartment';
  String _currency = 'USD';
  String _heatingType = 'central';
  bool _furnished = false;
  bool _didPrefill = false;
  bool _isSubmitting = false;
  final List<File> _selectedImages = [];

  bool get isEditing => widget.listingId != null;

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _cityController.dispose();
    _districtController.dispose();
    _addressController.dispose();
    _mapLabelController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    _roomsController.dispose();
    _areaController.dispose();
    _floorController.dispose();
    _totalFloorsController.dispose();
    _priceController.dispose();
    _bathroomsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authControllerProvider);
    final categoriesAsync = ref.watch(categoriesProvider);
    final detailAsync =
        isEditing ? ref.watch(listingDetailProvider(widget.listingId!)) : null;

    return Scaffold(
      appBar: AppBar(
        title: Text(isEditing
            ? context.tr('Edit property', 'Редактировать объект')
            : context.tr('Create property', 'Создать объект')),
      ),
      body: categoriesAsync.when(
        data: (categories) {
          if (isEditing) {
            return detailAsync!.when(
              data: (detail) {
                _prefill(detail);
                return _buildForm(context, authState, categories,
                    existingMedia: detail.mediaItems);
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stackTrace) =>
                  Center(child: Text(error.toString())),
            );
          }
          return _buildForm(context, authState, categories);
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stackTrace) => Center(child: Text(error.toString())),
      ),
    );
  }

  Widget _buildForm(
    BuildContext context,
    AuthState authState,
    List<CategoryOption> categories, {
    List<dynamic> existingMedia = const [],
  }) {
    return Form(
      key: _formKey,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          DropdownButtonFormField<String>(
            initialValue: _purpose,
            decoration:
                InputDecoration(labelText: context.tr('Purpose', 'Цель')),
            items: [
              DropdownMenuItem(
                  value: 'rent', child: Text(context.tr('Rent', 'Аренда'))),
              DropdownMenuItem(
                  value: 'sale', child: Text(context.tr('Sale', 'Продажа'))),
            ],
            onChanged: (value) => setState(() => _purpose = value ?? 'rent'),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _propertyType,
            decoration: InputDecoration(
                labelText: context.tr('Property type', 'Тип объекта')),
            items: [
              DropdownMenuItem(
                  value: 'apartment',
                  child: Text(context.tr('Apartment', 'Квартира'))),
              DropdownMenuItem(
                  value: 'house', child: Text(context.tr('House', 'Дом'))),
            ],
            onChanged: (value) =>
                setState(() => _propertyType = value ?? 'apartment'),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _titleController,
            decoration:
                InputDecoration(labelText: context.tr('Title', 'Заголовок')),
            validator: (value) => value == null || value.trim().length < 5
                ? context.tr('At least 5 characters.', 'Минимум 5 символов.')
                : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _descriptionController,
            decoration: InputDecoration(
                labelText: context.tr('Description', 'Описание')),
            minLines: 4,
            maxLines: 6,
            validator: (value) => value == null || value.trim().length < 20
                ? context.tr('At least 20 characters.', 'Минимум 20 символов.')
                : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _cityController,
            decoration: InputDecoration(labelText: context.tr('City', 'Город')),
            validator: (value) => value == null || value.trim().length < 2
                ? context.tr('Enter a city.', 'Укажите город.')
                : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _districtController,
            decoration: InputDecoration(
                labelText: context.tr('District / area', 'Район / зона')),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _addressController,
            decoration:
                InputDecoration(labelText: context.tr('Address text', 'Адрес')),
            validator: (value) => value == null || value.trim().length < 5
                ? context.tr('Enter the address.', 'Укажите адрес.')
                : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _mapLabelController,
            decoration: InputDecoration(
                labelText: context.tr('Map label', 'Подпись на карте')),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _latitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Latitude'),
                  validator: (value) =>
                      value == null || double.tryParse(value.trim()) == null
                          ? context.tr('Latitude is required.', 'Нужна широта.')
                          : null,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _longitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Longitude'),
                  validator: (value) => value == null ||
                          double.tryParse(value.trim()) == null
                      ? context.tr('Longitude is required.', 'Нужна долгота.')
                      : null,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            context.tr('Tap the map to place the property pin.',
                'Нажмите на карту, чтобы поставить метку объекта.'),
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 8),
          MapPreview(
            latitude: double.tryParse(_latitudeController.text),
            longitude: double.tryParse(_longitudeController.text),
            interactive: true,
            onTap: (latitude, longitude) {
              setState(() {
                _latitudeController.text = latitude.toStringAsFixed(6);
                _longitudeController.text = longitude.toStringAsFixed(6);
              });
            },
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _roomsController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                      labelText: context.tr('Rooms', 'Комнаты')),
                  validator: (value) =>
                      value == null || int.tryParse(value.trim()) == null
                          ? context.tr(
                              'Enter room count.', 'Укажите количество комнат.')
                          : null,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _areaController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                      labelText: context.tr('Area (m²)', 'Площадь (м²)')),
                  validator: (value) =>
                      value == null || double.tryParse(value.trim()) == null
                          ? context.tr('Enter area.', 'Укажите площадь.')
                          : null,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _floorController,
                  keyboardType: TextInputType.number,
                  decoration:
                      InputDecoration(labelText: context.tr('Floor', 'Этаж')),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _totalFloorsController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                      labelText: context.tr('Total floors', 'Всего этажей')),
                  validator: (value) {
                    if (_propertyType == 'apartment' &&
                        (value == null || value.trim().isEmpty)) {
                      return context.tr('Required for apartments.',
                          'Обязательно для квартир.');
                    }
                    return null;
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _priceController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration:
                      InputDecoration(labelText: context.tr('Price', 'Цена')),
                  validator: (value) =>
                      value == null || double.tryParse(value.trim()) == null
                          ? context.tr('Enter price.', 'Укажите цену.')
                          : null,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _currency,
                  decoration: InputDecoration(
                      labelText: context.tr('Currency', 'Валюта')),
                  items: const [
                    DropdownMenuItem(value: 'USD', child: Text('USD')),
                    DropdownMenuItem(value: 'KGS', child: Text('KGS')),
                  ],
                  onChanged: (value) =>
                      setState(() => _currency = value ?? 'USD'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _bathroomsController,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration:
                InputDecoration(labelText: context.tr('Bathrooms', 'Санузлы')),
            validator: (value) =>
                value == null || double.tryParse(value.trim()) == null
                    ? context.tr(
                        'Enter bathroom count.', 'Укажите количество санузлов.')
                    : null,
          ),
          if (_propertyType == 'apartment') ...[
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _heatingType,
              decoration: InputDecoration(
                  labelText: context.tr('Heating type', 'Тип отопления')),
              items: const [
                DropdownMenuItem(value: 'central', child: Text('Central')),
                DropdownMenuItem(value: 'gas', child: Text('Gas')),
                DropdownMenuItem(value: 'electric', child: Text('Electric')),
              ],
              onChanged: (value) =>
                  setState(() => _heatingType = value ?? 'central'),
            ),
          ],
          const SizedBox(height: 8),
          SwitchListTile(
            value: _furnished,
            title: Text(context.tr('Furnished', 'С мебелью')),
            contentPadding: EdgeInsets.zero,
            onChanged: (value) => setState(() => _furnished = value),
          ),
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(context.tr('Photos', 'Фото'),
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final image in _selectedImages)
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.file(image,
                              width: 88, height: 88, fit: BoxFit.cover),
                        ),
                      for (final media in existingMedia)
                        if (media.mediaType == 'image')
                          ClipRRect(
                            borderRadius: BorderRadius.circular(12),
                            child: NetworkMediaImage(
                              assetKey: media.assetKey,
                              width: 88,
                              height: 88,
                            ),
                          ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  FilledButton.tonalIcon(
                    onPressed: _pickImages,
                    icon: const Icon(Icons.photo_library_outlined),
                    label: Text(context.tr('Add photos', 'Добавить фото')),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    context.tr(
                      'Video tours are supported by the backend, but the mobile upload/display UI is intentionally deferred to the next prompt.',
                      'Видео-тур поддерживается бэкендом, но мобильный интерфейс загрузки и показа отложен до следующего шага.',
                    ),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _isSubmitting
                      ? null
                      : () => _submit(
                            authState: authState,
                            categories: categories,
                            publishNow: false,
                          ),
                  child: Text(_isSubmitting
                      ? context.tr('Saving...', 'Сохраняем...')
                      : context.tr('Save draft', 'Сохранить черновик')),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: FilledButton(
                  onPressed: _isSubmitting
                      ? null
                      : () => _submit(
                            authState: authState,
                            categories: categories,
                            publishNow: true,
                          ),
                  child: Text(context.tr(
                      'Save and publish', 'Сохранить и опубликовать')),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _prefill(dynamic detail) {
    if (_didPrefill) {
      return;
    }
    _didPrefill = true;
    _titleController.text = detail.title;
    _descriptionController.text = detail.description;
    _cityController.text = detail.city;
    _districtController.text = detail.district ?? '';
    _addressController.text = detail.addressText;
    _mapLabelController.text = detail.mapLabel ?? '';
    _latitudeController.text = detail.latitude.toString();
    _longitudeController.text = detail.longitude.toString();
    _roomsController.text = detail.roomCount.toString();
    _areaController.text = detail.areaSqm;
    _floorController.text = detail.floor?.toString() ?? '';
    _totalFloorsController.text = detail.totalFloors?.toString() ?? '';
    _priceController.text = detail.priceAmount;
    _purpose = detail.purpose;
    _propertyType = detail.propertyType;
    _currency = detail.currencyCode;
    _furnished = detail.furnished ?? false;
    for (final attribute in detail.attributeValues) {
      if (attribute.attributeCode == 'bathrooms' &&
          attribute.numericValue != null) {
        _bathroomsController.text = attribute.numericValue.toString();
      }
      if (attribute.attributeCode == 'heating_type' &&
          attribute.optionValue != null) {
        _heatingType = attribute.optionValue!;
      }
    }
  }

  Future<void> _pickImages() async {
    final images = await _picker.pickMultiImage(imageQuality: 85);
    if (!mounted || images.isEmpty) {
      return;
    }
    setState(() {
      _selectedImages.addAll(images.map((item) => File(item.path)));
    });
  }

  Future<void> _submit({
    required AuthState authState,
    required List<CategoryOption> categories,
    required bool publishNow,
  }) async {
    if (!_formKey.currentState!.validate() || authState.session == null) {
      return;
    }
    final category = _resolveCategory(categories);
    if (category == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(context.tr(
                'No matching category is configured for this property type.',
                'Для этого типа объекта не настроена подходящая категория.'))),
      );
      return;
    }

    final floor = int.tryParse(_floorController.text.trim());
    final totalFloors = int.tryParse(_totalFloorsController.text.trim());
    if (floor != null && totalFloors != null && floor > totalFloors) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(context.tr('Floor cannot exceed total floors.',
                'Этаж не может быть больше общего количества этажей.'))),
      );
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      final repository = ref.read(listingsRepositoryProvider);
      final locale = ref.read(authControllerProvider).session!.user.locale;
      final data = ListingFormData(
        publicId: widget.listingId,
        categoryPublicId: category.publicId,
        title: _titleController.text,
        description: _descriptionController.text,
        purpose: _purpose,
        propertyType: _propertyType,
        priceAmount: _priceController.text,
        currencyCode: _currency,
        city: _cityController.text,
        district: _districtController.text,
        addressText: _addressController.text,
        mapLabel: _mapLabelController.text,
        latitude: _latitudeController.text,
        longitude: _longitudeController.text,
        roomCount: _roomsController.text,
        areaSqm: _areaController.text,
        floor: _floorController.text,
        totalFloors: _totalFloorsController.text,
        furnished: _furnished,
        heatingType: _heatingType,
        bathrooms: _bathroomsController.text,
      );
      final detail = isEditing
          ? await repository.updateListing(
              accessToken: authState.session!.accessToken,
              locale: locale,
              data: data,
            )
          : await repository.createListing(
              accessToken: authState.session!.accessToken,
              locale: locale,
              data: data,
            );
      if (_selectedImages.isNotEmpty) {
        await repository.uploadListingImages(
          accessToken: authState.session!.accessToken,
          listingId: detail.publicId,
          images: _selectedImages,
        );
      }
      if (publishNow) {
        await repository.publishListing(
          accessToken: authState.session!.accessToken,
          listingId: detail.publicId,
        );
      }
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(detail.publicId));
      if (!mounted) {
        return;
      }
      context.go('/listing/${detail.publicId}');
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(error.toString())));
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  CategoryOption? _resolveCategory(List<CategoryOption> categories) {
    final preferredSlug =
        _propertyType == 'apartment' ? 'apartments' : 'houses';
    for (final category in categories) {
      if (category.slug == preferredSlug ||
          category.slug.contains(_propertyType)) {
        return category;
      }
    }
    return categories.isEmpty ? null : categories.first;
  }
}
