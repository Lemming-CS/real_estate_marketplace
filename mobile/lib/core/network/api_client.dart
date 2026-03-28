import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, {this.code, this.statusCode});

  final String message;
  final String? code;
  final int? statusCode;

  @override
  String toString() => 'ApiException($statusCode, $code, $message)';
}

class ApiClient {
  ApiClient({
    required this.baseUrl,
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Future<Map<String, dynamic>> getJson(
    String path, {
    String? accessToken,
    Map<String, String?> query = const {},
  }) async {
    final response = await _client.get(
      _uri(path, query),
      headers: _headers(accessToken: accessToken),
    );
    return _decodeMap(response);
  }

  Future<List<dynamic>> getJsonList(
    String path, {
    String? accessToken,
    Map<String, String?> query = const {},
  }) async {
    final response = await _client.get(
      _uri(path, query),
      headers: _headers(accessToken: accessToken),
    );
    return _decodeList(response);
  }

  Future<Map<String, dynamic>> postJson(
    String path, {
    String? accessToken,
    Map<String, dynamic>? body,
    Map<String, String?> query = const {},
  }) async {
    final response = await _client.post(
      _uri(path, query),
      headers: _headers(accessToken: accessToken),
      body: jsonEncode(body ?? <String, dynamic>{}),
    );
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> patchJson(
    String path, {
    String? accessToken,
    Map<String, dynamic>? body,
    Map<String, String?> query = const {},
  }) async {
    final response = await _client.patch(
      _uri(path, query),
      headers: _headers(accessToken: accessToken),
      body: jsonEncode(body ?? <String, dynamic>{}),
    );
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> deleteJson(
    String path, {
    String? accessToken,
  }) async {
    final response = await _client.delete(
      _uri(path, const {}),
      headers: _headers(accessToken: accessToken),
    );
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> postMultipart(
    String path, {
    required List<File> files,
    String? accessToken,
    String fileField = 'upload',
    Map<String, String> fields = const {},
  }) async {
    final request = http.MultipartRequest('POST', _uri(path, const {}))
      ..headers.addAll(_multipartHeaders(accessToken: accessToken))
      ..fields.addAll(fields);
    for (final file in files) {
      request.files
          .add(await http.MultipartFile.fromPath(fileField, file.path));
    }
    final streamed = await request.send();
    return _decodeMap(await http.Response.fromStream(streamed));
  }

  Uri _uri(String path, Map<String, String?> query) {
    final sanitizedPath = path.startsWith('/') ? path.substring(1) : path;
    final uri = Uri.parse('$baseUrl/$sanitizedPath');
    final filtered = <String, String>{};
    for (final entry in query.entries) {
      final value = entry.value;
      if (value != null && value.isNotEmpty) {
        filtered[entry.key] = value;
      }
    }
    return uri.replace(queryParameters: filtered.isEmpty ? null : filtered);
  }

  Map<String, String> _headers({String? accessToken}) {
    final headers = <String, String>{'Content-Type': 'application/json'};
    if (accessToken != null && accessToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $accessToken';
    }
    return headers;
  }

  Map<String, String> _multipartHeaders({String? accessToken}) {
    final headers = <String, String>{};
    if (accessToken != null && accessToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $accessToken';
    }
    return headers;
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    final payload = _decode(response);
    if (payload is Map<String, dynamic>) {
      return payload;
    }
    throw const ApiException('Unexpected response shape.');
  }

  List<dynamic> _decodeList(http.Response response) {
    final payload = _decode(response);
    if (payload is List<dynamic>) {
      return payload;
    }
    throw const ApiException('Unexpected response shape.');
  }

  dynamic _decode(http.Response response) {
    final body = response.body.isEmpty ? null : jsonDecode(response.body);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return body;
    }
    if (body is Map<String, dynamic> && body['error'] is Map<String, dynamic>) {
      final error = body['error'] as Map<String, dynamic>;
      throw ApiException(
        (error['message'] ?? 'Request failed.').toString(),
        code: error['code']?.toString(),
        statusCode: response.statusCode,
      );
    }
    throw ApiException(
      'Request failed with status ${response.statusCode}.',
      statusCode: response.statusCode,
    );
  }
}
