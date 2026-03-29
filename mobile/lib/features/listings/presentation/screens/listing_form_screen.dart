import 'dart:io';

import 'package:electronics_marketplace_mobile/core/localization/app_strings.dart';
import 'package:electronics_marketplace_mobile/features/auth/presentation/controllers/auth_controller.dart';
import 'package:electronics_marketplace_mobile/features/listings/data/listings_repository.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/category_models.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_form_data.dart';
import 'package:electronics_marketplace_mobile/features/listings/domain/listing_models.dart';
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
  bool _isPrefilling = false;
  bool _isSubmitting = false;
  String? _submitError;
  AutovalidateMode _autovalidateMode = AutovalidateMode.disabled;
  final List<File> _selectedImages = [];
  File? _selectedVideo;
  final List<ListingMedia> _existingMedia = [];
  late final Listenable _formInputsListenable;
  late final Listenable _locationInputsListenable;

  bool get isEditing => widget.listingId != null;

  @override
  void initState() {
    super.initState();
    _formInputsListenable = Listenable.merge(_textControllers);
    _locationInputsListenable =
        Listenable.merge([_latitudeController, _longitudeController]);
    for (final controller in _textControllers) {
      controller.addListener(_handleFormChanged);
    }
  }

  @override
  void dispose() {
    for (final controller in _textControllers) {
      controller.removeListener(_handleFormChanged);
    }
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

  List<TextEditingController> get _textControllers => [
        _titleController,
        _descriptionController,
        _cityController,
        _districtController,
        _addressController,
        _mapLabelController,
        _latitudeController,
        _longitudeController,
        _roomsController,
        _areaController,
        _floorController,
        _totalFloorsController,
        _priceController,
        _bathroomsController,
      ];

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
        actions: [
          IconButton(
            onPressed: _isSubmitting ? null : () => context.go('/'),
            icon: const Icon(Icons.home_outlined),
            tooltip: context.tr('Home', 'Главная'),
          ),
          if (isEditing)
            IconButton(
              onPressed: _isSubmitting ? null : () => _deleteListing(authState),
              icon: const Icon(Icons.delete_outline),
              tooltip: context.tr('Delete', 'Удалить'),
            ),
          if (context.canPop())
            TextButton(
              onPressed: _isSubmitting ? null : () => context.pop(),
              child: Text(context.tr('Cancel', 'Отмена')),
            ),
        ],
      ),
      body: categoriesAsync.when(
        data: (categories) {
          if (isEditing) {
            return detailAsync!.when(
              data: (detail) {
                _prefill(detail);
                return _buildForm(
                  context,
                  authState,
                  categories,
                  existingMedia: _existingMedia,
                );
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
    List<ListingMedia> existingMedia = const [],
  }) {
    return Form(
      key: _formKey,
      autovalidateMode: _autovalidateMode,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            context.tr(
              'Fields marked with * are required. Optional fields are labeled explicitly.',
              'Поля со знаком * обязательны. Необязательные поля отмечены отдельно.',
            ),
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: 12),
          if (_submitError != null) ...[
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  _submitError!,
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onErrorContainer,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
          ],
          DropdownButtonFormField<String>(
            initialValue: _purpose,
            decoration: _requiredDecoration(
              context,
              'Purpose',
              'Цель',
            ),
            items: [
              DropdownMenuItem(
                  value: 'rent', child: Text(context.tr('Rent', 'Аренда'))),
              DropdownMenuItem(
                  value: 'sale', child: Text(context.tr('Sale', 'Продажа'))),
            ],
            onChanged: (value) => setState(() {
              _purpose = value ?? 'rent';
              _submitError = null;
            }),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _propertyType,
            decoration: _requiredDecoration(
              context,
              'Property type',
              'Тип объекта',
            ),
            items: [
              DropdownMenuItem(
                  value: 'apartment',
                  child: Text(context.tr('Apartment', 'Квартира'))),
              DropdownMenuItem(
                  value: 'house', child: Text(context.tr('House', 'Дом'))),
            ],
            onChanged: (value) => setState(() {
              _propertyType = value ?? 'apartment';
              _submitError = null;
            }),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _titleController,
            decoration: _requiredDecoration(
              context,
              'Title',
              'Заголовок',
              helperText: context.tr(
                'Minimum 5 characters.',
                'Минимум 5 символов.',
              ),
            ),
            validator: (value) => _validateTitle(context, value),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _descriptionController,
            decoration: _requiredDecoration(
              context,
              'Description',
              'Описание',
              helperText: context.tr(
                'Minimum 20 characters.',
                'Минимум 20 символов.',
              ),
            ),
            minLines: 4,
            maxLines: 6,
            validator: (value) => _validateDescription(context, value),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _cityController,
            decoration: _requiredDecoration(
              context,
              'City',
              'Город',
              helperText: context.tr(
                'Minimum 2 characters.',
                'Минимум 2 символа.',
              ),
            ),
            validator: (value) => _validateCity(context, value),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _districtController,
            decoration: _optionalDecoration(
              context,
              'District / area',
              'Район / зона',
            ),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _addressController,
            decoration: _requiredDecoration(
              context,
              'Address text',
              'Адрес',
              helperText: context.tr(
                'Minimum 5 characters.',
                'Минимум 5 символов.',
              ),
            ),
            validator: (value) => _validateAddress(context, value),
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _mapLabelController,
            decoration: _optionalDecoration(
              context,
              'Map label',
              'Подпись на карте',
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _latitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: _requiredDecoration(
                    context,
                    'Latitude',
                    'Широта',
                    helperText: context.tr(
                      'From -90 to 90.',
                      'Диапазон от -90 до 90.',
                    ),
                  ),
                  validator: (value) => _validateLatitude(context, value),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _longitudeController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: _requiredDecoration(
                    context,
                    'Longitude',
                    'Долгота',
                    helperText: context.tr(
                      'From -180 to 180.',
                      'Диапазон от -180 до 180.',
                    ),
                  ),
                  validator: (value) => _validateLongitude(context, value),
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
          ListenableBuilder(
            listenable: _locationInputsListenable,
            builder: (context, child) {
              return MapPreview(
                latitude: double.tryParse(_latitudeController.text),
                longitude: double.tryParse(_longitudeController.text),
                interactive: true,
                onTap: (latitude, longitude) {
                  setState(() {
                    _latitudeController.text = latitude.toStringAsFixed(6);
                    _longitudeController.text = longitude.toStringAsFixed(6);
                    _submitError = null;
                  });
                },
              );
            },
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextFormField(
                  controller: _roomsController,
                  keyboardType: TextInputType.number,
                  decoration: _requiredDecoration(
                    context,
                    'Rooms',
                    'Комнаты',
                    helperText: context.tr(
                      'Whole number, at least 1.',
                      'Целое число, минимум 1.',
                    ),
                  ),
                  validator: (value) => _validateRoomCount(context, value),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _areaController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: _requiredDecoration(
                    context,
                    'Area (m²)',
                    'Площадь (м²)',
                    helperText: context.tr(
                      'Must be greater than 0.',
                      'Должна быть больше 0.',
                    ),
                  ),
                  validator: (value) => _validateArea(context, value),
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
                  decoration: _optionalDecoration(context, 'Floor', 'Этаж'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: TextFormField(
                  controller: _totalFloorsController,
                  keyboardType: TextInputType.number,
                  decoration: _propertyType == 'apartment'
                      ? _requiredDecoration(
                          context,
                          'Total floors',
                          'Всего этажей',
                          helperText: context.tr(
                            'Required for apartments.',
                            'Обязательно для квартир.',
                          ),
                        )
                      : _optionalDecoration(
                          context,
                          'Total floors',
                          'Всего этажей',
                        ),
                  validator: (value) => _validateTotalFloors(context, value),
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
                  decoration: _requiredDecoration(
                    context,
                    'Price',
                    'Цена',
                    helperText: context.tr(
                      'Must be greater than 0.',
                      'Должна быть больше 0.',
                    ),
                  ),
                  validator: (value) => _validatePrice(context, value),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _currency,
                  decoration: _requiredDecoration(
                    context,
                    'Currency',
                    'Валюта',
                  ),
                  items: const [
                    DropdownMenuItem(value: 'USD', child: Text('USD')),
                    DropdownMenuItem(value: 'KGS', child: Text('KGS')),
                  ],
                  onChanged: (value) => setState(() {
                    _currency = value ?? 'USD';
                    _submitError = null;
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _bathroomsController,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: _requiredDecoration(
              context,
              'Bathrooms',
              'Санузлы',
              helperText: context.tr(
                'Must be greater than 0.',
                'Должно быть больше 0.',
              ),
            ),
            validator: (value) => _validateBathrooms(context, value),
          ),
          if (_propertyType == 'apartment') ...[
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _heatingType,
              decoration: _optionalDecoration(
                context,
                'Heating type',
                'Тип отопления',
              ),
              items: const [
                DropdownMenuItem(value: 'central', child: Text('Central')),
                DropdownMenuItem(value: 'gas', child: Text('Gas')),
                DropdownMenuItem(value: 'electric', child: Text('Electric')),
              ],
              onChanged: (value) => setState(() {
                _heatingType = value ?? 'central';
                _submitError = null;
              }),
            ),
          ],
          const SizedBox(height: 8),
          SwitchListTile(
            value: _furnished,
            title: Text(context.tr('Furnished', 'С мебелью')),
            contentPadding: EdgeInsets.zero,
            onChanged: (value) => setState(() {
              _furnished = value;
              _submitError = null;
            }),
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
                  Text(
                    context.tr(
                      'Media is optional. Add photos now if you have them.',
                      'Медиа необязательно. Добавьте фото сейчас, если они у вас есть.',
                    ),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final image in _selectedImages)
                        Stack(
                          children: [
                            ClipRRect(
                              borderRadius: BorderRadius.circular(12),
                              child: Image.file(image,
                                  width: 88, height: 88, fit: BoxFit.cover),
                            ),
                            Positioned(
                              top: 4,
                              right: 4,
                              child: CircleAvatar(
                                radius: 14,
                                backgroundColor: Colors.black54,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  onPressed: _isSubmitting
                                      ? null
                                      : () => setState(() {
                                            _selectedImages.remove(image);
                                          }),
                                  icon: const Icon(
                                    Icons.close,
                                    size: 14,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                      if (_selectedVideo != null)
                        Stack(
                          children: [
                            Container(
                              width: 88,
                              height: 88,
                              decoration: BoxDecoration(
                                color: Colors.grey.shade200,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              alignment: Alignment.center,
                              child: const Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.videocam_outlined),
                                  SizedBox(height: 4),
                                  Text('MP4'),
                                ],
                              ),
                            ),
                            Positioned(
                              top: 4,
                              right: 4,
                              child: CircleAvatar(
                                radius: 14,
                                backgroundColor: Colors.black54,
                                child: IconButton(
                                  padding: EdgeInsets.zero,
                                  onPressed: _isSubmitting
                                      ? null
                                      : () => setState(() {
                                            _selectedVideo = null;
                                          }),
                                  icon: const Icon(
                                    Icons.close,
                                    size: 14,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                  if (existingMedia.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    Text(
                      context.tr(
                        'Existing media',
                        'Текущие медиа',
                      ),
                      style: Theme.of(context).textTheme.titleSmall,
                    ),
                    const SizedBox(height: 8),
                    ...List.generate(existingMedia.length, (index) {
                      final media = existingMedia[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(12),
                                child: media.mediaType == 'image'
                                    ? NetworkMediaImage(
                                        assetKey: media.assetKey,
                                        width: 88,
                                        height: 88,
                                      )
                                    : Container(
                                        width: 88,
                                        height: 88,
                                        color: Colors.grey.shade200,
                                        alignment: Alignment.center,
                                        child: const Icon(
                                          Icons.videocam_outlined,
                                        ),
                                      ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      media.isPrimary
                                          ? context.tr(
                                              'Primary media',
                                              'Основное медиа',
                                            )
                                          : context.tr(
                                              'Media item',
                                              'Медиафайл',
                                            ),
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleSmall,
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      media.mimeType,
                                      style:
                                          Theme.of(context).textTheme.bodySmall,
                                    ),
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 8,
                                      children: [
                                        if (media.mediaType == 'image')
                                          OutlinedButton(
                                            onPressed: _isSubmitting
                                                ? null
                                                : () => _replaceExistingMedia(
                                                      authState: authState,
                                                      media: media,
                                                    ),
                                            child: Text(
                                              context.tr(
                                                'Replace',
                                                'Заменить',
                                              ),
                                            ),
                                          ),
                                        if (!media.isPrimary &&
                                            media.mediaType == 'image')
                                          OutlinedButton(
                                            onPressed: _isSubmitting
                                                ? null
                                                : () => _setPrimaryMedia(
                                                      authState: authState,
                                                      media: media,
                                                    ),
                                            child: Text(
                                              context.tr(
                                                'Set primary',
                                                'Сделать основным',
                                              ),
                                            ),
                                          ),
                                        OutlinedButton(
                                          onPressed: _isSubmitting || index == 0
                                              ? null
                                              : () => _moveMedia(
                                                    authState: authState,
                                                    index: index,
                                                    direction: -1,
                                                  ),
                                          child:
                                              Text(context.tr('Up', 'Вверх')),
                                        ),
                                        OutlinedButton(
                                          onPressed: _isSubmitting ||
                                                  index ==
                                                      existingMedia.length - 1
                                              ? null
                                              : () => _moveMedia(
                                                    authState: authState,
                                                    index: index,
                                                    direction: 1,
                                                  ),
                                          child:
                                              Text(context.tr('Down', 'Вниз')),
                                        ),
                                        TextButton(
                                          onPressed: _isSubmitting
                                              ? null
                                              : () => _deleteExistingMedia(
                                                    authState: authState,
                                                    media: media,
                                                  ),
                                          child: Text(
                                            context.tr('Delete', 'Удалить'),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }),
                  ],
                  const SizedBox(height: 12),
                  FilledButton.tonalIcon(
                    onPressed: _isSubmitting ? null : _pickImages,
                    icon: const Icon(Icons.photo_library_outlined),
                    label: Text(context.tr('Add photos', 'Добавить фото')),
                  ),
                  const SizedBox(height: 12),
                  FilledButton.tonalIcon(
                    onPressed: _isSubmitting ? null : _pickVideo,
                    icon: const Icon(Icons.video_library_outlined),
                    label: Text(
                      _selectedVideo == null
                          ? context.tr('Add video tour', 'Добавить видео-тур')
                          : context.tr(
                              'Replace video tour',
                              'Заменить видео-тур',
                            ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    context.tr(
                      'Media is optional. You can upload photos and one optional short MP4 video tour.',
                      'Медиа необязательно. Вы можете загрузить фото и один дополнительный короткий MP4 видео-тур.',
                    ),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),
          ListenableBuilder(
            listenable: _formInputsListenable,
            builder: (context, child) {
              final canSaveDraft =
                  !_isSubmitting && _isFormLocallyValid(context);
              final canPublish = canSaveDraft;
              return Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: canSaveDraft
                          ? () => _submit(
                                authState: authState,
                                categories: categories,
                                publishNow: false,
                              )
                          : null,
                      child: Text(_isSubmitting
                          ? context.tr('Saving...', 'Сохраняем...')
                          : context.tr('Save draft', 'Сохранить черновик')),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: FilledButton(
                      onPressed: canPublish
                          ? () => _submit(
                                authState: authState,
                                categories: categories,
                                publishNow: true,
                              )
                          : null,
                      child: Text(context.tr(
                          'Save and publish', 'Сохранить и опубликовать')),
                    ),
                  ),
                ],
              );
            },
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
    _isPrefilling = true;
    _existingMedia
      ..clear()
      ..addAll(detail.mediaItems as List<ListingMedia>);
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
    _isPrefilling = false;
  }

  Future<void> _pickImages() async {
    final images = await _picker.pickMultiImage(imageQuality: 85);
    if (!mounted || images.isEmpty) {
      return;
    }
    setState(() {
      _selectedImages.addAll(images.map((item) => File(item.path)));
      _submitError = null;
    });
  }

  Future<void> _pickVideo() async {
    final picked = await _picker.pickVideo(source: ImageSource.gallery);
    if (!mounted || picked == null) {
      return;
    }
    setState(() {
      _selectedVideo = File(picked.path);
      _submitError = null;
    });
  }

  Future<void> _deleteExistingMedia({
    required AuthState authState,
    required ListingMedia media,
  }) async {
    final listingId = widget.listingId;
    final accessToken = authState.session?.accessToken;
    if (listingId == null || accessToken == null) {
      return;
    }
    final repository = ref.read(listingsRepositoryProvider);
    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    try {
      await repository.deleteListingImage(
        accessToken: accessToken,
        listingId: listingId,
        mediaId: media.publicId,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _existingMedia.removeWhere((item) => item.publicId == media.publicId);
      });
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(listingId));
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _replaceExistingMedia({
    required AuthState authState,
    required ListingMedia media,
  }) async {
    final listingId = widget.listingId;
    final accessToken = authState.session?.accessToken;
    if (listingId == null || accessToken == null) {
      return;
    }
    final picked =
        await _picker.pickImage(source: ImageSource.gallery, imageQuality: 85);
    if (!mounted || picked == null) {
      return;
    }
    final repository = ref.read(listingsRepositoryProvider);
    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    try {
      final updated = await repository.replaceListingImage(
        accessToken: accessToken,
        listingId: listingId,
        mediaId: media.publicId,
        image: File(picked.path),
      );
      if (!mounted) {
        return;
      }
      final nextMedia = List<ListingMedia>.from(_existingMedia);
      final index =
          nextMedia.indexWhere((item) => item.publicId == media.publicId);
      if (index >= 0) {
        nextMedia[index] = updated;
      }
      _applyExistingMedia(nextMedia);
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(listingId));
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _moveMedia({
    required AuthState authState,
    required int index,
    required int direction,
  }) async {
    final listingId = widget.listingId;
    final accessToken = authState.session?.accessToken;
    if (listingId == null || accessToken == null) {
      return;
    }
    final nextIndex = index + direction;
    if (nextIndex < 0 || nextIndex >= _existingMedia.length) {
      return;
    }
    final reordered = List<ListingMedia>.from(_existingMedia);
    final item = reordered.removeAt(index);
    reordered.insert(nextIndex, item);
    final repository = ref.read(listingsRepositoryProvider);
    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    try {
      final response = await repository.reorderListingMedia(
        accessToken: accessToken,
        listingId: listingId,
        mediaIds: reordered.map((media) => media.publicId).toList(),
      );
      if (!mounted) {
        return;
      }
      _applyExistingMedia(response);
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(listingId));
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _setPrimaryMedia({
    required AuthState authState,
    required ListingMedia media,
  }) async {
    final listingId = widget.listingId;
    final accessToken = authState.session?.accessToken;
    if (listingId == null || accessToken == null) {
      return;
    }
    final repository = ref.read(listingsRepositoryProvider);
    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    try {
      final response = await repository.setPrimaryListingMedia(
        accessToken: accessToken,
        listingId: listingId,
        mediaId: media.publicId,
      );
      if (!mounted) {
        return;
      }
      _applyExistingMedia(response);
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(listingId));
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _submit({
    required AuthState authState,
    required List<CategoryOption> categories,
    required bool publishNow,
  }) async {
    if (!_formKey.currentState!.validate() || authState.session == null) {
      setState(() {
        _autovalidateMode = AutovalidateMode.always;
      });
      return;
    }
    final category = _resolveCategory(categories);
    if (category == null) {
      setState(() {
        _submitError = context.tr(
          'No matching category is configured for this property type.',
          'Для этого типа объекта не настроена подходящая категория.',
        );
      });
      return;
    }

    final floor = int.tryParse(_floorController.text.trim());
    final totalFloors = int.tryParse(_totalFloorsController.text.trim());
    if (floor != null && totalFloors != null && floor > totalFloors) {
      setState(() {
        _submitError = context.tr(
          'Floor cannot exceed total floors.',
          'Этаж не может быть больше общего количества этажей.',
        );
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    final repository = ref.read(listingsRepositoryProvider);
    final locale = authState.session!.user.locale;
    final accessToken = authState.session!.accessToken;
    try {
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
              accessToken: accessToken,
              locale: locale,
              data: data,
            )
          : await repository.createListing(
              accessToken: accessToken,
              locale: locale,
              data: data,
            );
      if (!mounted) {
        return;
      }
      final uploads = <File>[
        ..._selectedImages,
        if (_selectedVideo != null) _selectedVideo!,
      ];
      if (uploads.isNotEmpty) {
        await repository.uploadListingMedia(
          accessToken: accessToken,
          listingId: detail.publicId,
          files: uploads,
        );
        if (!mounted) {
          return;
        }
      }
      if (publishNow) {
        await repository.publishListing(
          accessToken: accessToken,
          listingId: detail.publicId,
        );
        if (!mounted) {
          return;
        }
      }
      if (!mounted) {
        return;
      }
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(detail.publicId));
      context.push('/listing/${detail.publicId}');
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }

  Future<void> _deleteListing(AuthState authState) async {
    final listingId = widget.listingId;
    final session = authState.session;
    if (listingId == null || session == null) {
      return;
    }
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.tr('Delete listing?', 'Удалить объявление?')),
        content: Text(
          context.tr(
            'This will remove the listing from the marketplace and favorites. Active promotions must be ended first.',
            'Это уберет объявление из маркетплейса и избранного. Активные продвижения нужно завершить заранее.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(context.tr('Cancel', 'Отмена')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(context.tr('Delete', 'Удалить')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) {
      return;
    }

    setState(() {
      _isSubmitting = true;
      _submitError = null;
    });
    final repository = ref.read(listingsRepositoryProvider);
    try {
      await repository.deleteListing(
        accessToken: session.accessToken,
        listingId: listingId,
      );
      if (!mounted) {
        return;
      }
      ref.invalidate(homeListingsProvider);
      ref.invalidate(myListingsProvider);
      ref.invalidate(listingDetailProvider(listingId));
      context.go('/my-listings');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(context.tr('Listing deleted.', 'Объявление удалено.')),
        ),
      );
    } catch (error) {
      if (mounted) {
        setState(() {
          _submitError = error.toString();
        });
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

  void _handleFormChanged() {
    if (!mounted || _isPrefilling || _submitError == null) {
      return;
    }
    setState(() {
      _submitError = null;
    });
  }

  void _applyExistingMedia(List<ListingMedia> media) {
    setState(() {
      _existingMedia
        ..clear()
        ..addAll(
          media.toList()
            ..sort(
              (a, b) => a.sortOrder.compareTo(b.sortOrder),
            ),
        );
    });
  }

  bool _isFormLocallyValid(BuildContext context) {
    return _validateTitle(context, _titleController.text) == null &&
        _validateDescription(context, _descriptionController.text) == null &&
        _validateCity(context, _cityController.text) == null &&
        _validateAddress(context, _addressController.text) == null &&
        _validatePrice(context, _priceController.text) == null &&
        _validateLatitude(context, _latitudeController.text) == null &&
        _validateLongitude(context, _longitudeController.text) == null &&
        _validateRoomCount(context, _roomsController.text) == null &&
        _validateArea(context, _areaController.text) == null &&
        _validateBathrooms(context, _bathroomsController.text) == null &&
        _validateTotalFloors(context, _totalFloorsController.text) == null;
  }

  InputDecoration _requiredDecoration(
    BuildContext context,
    String englishLabel,
    String russianLabel, {
    String? helperText,
  }) {
    return InputDecoration(
      labelText: '${context.tr(englishLabel, russianLabel)} *',
      helperText: helperText,
    );
  }

  InputDecoration _optionalDecoration(
    BuildContext context,
    String englishLabel,
    String russianLabel, {
    String? helperText,
  }) {
    return InputDecoration(
      labelText:
          '${context.tr(englishLabel, russianLabel)} (${context.tr('Optional', 'Необязательно')})',
      helperText: helperText,
    );
  }

  String? _validateTitle(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Title is required.', 'Заголовок обязателен.');
    }
    if (trimmed.length < 5) {
      return context.tr(
        'Title must be at least 5 characters.',
        'Заголовок должен быть не короче 5 символов.',
      );
    }
    return null;
  }

  String? _validateDescription(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Description is required.', 'Описание обязательно.');
    }
    if (trimmed.length < 20) {
      return context.tr(
        'Description must be at least 20 characters.',
        'Описание должно быть не короче 20 символов.',
      );
    }
    return null;
  }

  String? _validateCity(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('City is required.', 'Город обязателен.');
    }
    if (trimmed.length < 2) {
      return context.tr(
        'City must be at least 2 characters.',
        'Название города должно быть не короче 2 символов.',
      );
    }
    return null;
  }

  String? _validateAddress(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Address is required.', 'Адрес обязателен.');
    }
    if (trimmed.length < 5) {
      return context.tr(
        'Address must be at least 5 characters.',
        'Адрес должен быть не короче 5 символов.',
      );
    }
    return null;
  }

  String? _validatePrice(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Price is required.', 'Цена обязательна.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return context.tr(
        'Enter a valid price.',
        'Укажите корректную цену.',
      );
    }
    return null;
  }

  String? _validateLatitude(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Latitude is required.', 'Нужна широта.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed < -90 || parsed > 90) {
      return context.tr(
        'Latitude must be between -90 and 90.',
        'Широта должна быть в диапазоне от -90 до 90.',
      );
    }
    return null;
  }

  String? _validateLongitude(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Longitude is required.', 'Нужна долгота.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed < -180 || parsed > 180) {
      return context.tr(
        'Longitude must be between -180 and 180.',
        'Долгота должна быть в диапазоне от -180 до 180.',
      );
    }
    return null;
  }

  String? _validateRoomCount(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr(
        'Room count is required.',
        'Количество комнат обязательно.',
      );
    }
    final parsed = int.tryParse(trimmed);
    if (parsed == null || parsed < 1) {
      return context.tr(
        'Enter a valid room count.',
        'Укажите корректное количество комнат.',
      );
    }
    return null;
  }

  String? _validateArea(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr('Area is required.', 'Площадь обязательна.');
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return context.tr(
        'Enter a valid area.',
        'Укажите корректную площадь.',
      );
    }
    return null;
  }

  String? _validateBathrooms(BuildContext context, String? value) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr(
        'Bathroom count is required.',
        'Количество санузлов обязательно.',
      );
    }
    final parsed = double.tryParse(trimmed);
    if (parsed == null || parsed <= 0) {
      return context.tr(
        'Enter a valid bathroom count.',
        'Укажите корректное количество санузлов.',
      );
    }
    return null;
  }

  String? _validateTotalFloors(BuildContext context, String? value) {
    if (_propertyType != 'apartment') {
      return null;
    }
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return context.tr(
        'Total floors are required for apartments.',
        'Для квартир нужно указать общее количество этажей.',
      );
    }
    final parsed = int.tryParse(trimmed);
    if (parsed == null || parsed < 1) {
      return context.tr(
        'Enter a valid total floor count.',
        'Укажите корректное общее количество этажей.',
      );
    }
    return null;
  }
}
