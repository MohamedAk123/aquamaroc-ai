import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../domain/models.dart';

class ApiException implements Exception {
  final String message;
  final bool incompatible;
  const ApiException(this.message, {this.incompatible = false});
  @override
  String toString() => message;
}

class ApiClient {
  final Uri base;
  final AppMode mode;
  final http.Client client;
  final Duration timeout;
  ApiClient({
    required String baseUrl,
    required this.mode,
    required this.client,
    this.timeout = const Duration(seconds: 15),
  }) : base = Uri.parse(baseUrl) {
    if (!['http', 'https'].contains(base.scheme) ||
        base.host.isEmpty ||
        base.hasQuery ||
        base.hasFragment ||
        base.userInfo.isNotEmpty) {
      throw const FormatException(
        'API_URL doit être une origine HTTP(S), sans identifiants',
      );
    }
  }
  String get namespace =>
      '${base.toString().replaceFirst(RegExp(r'/+$'), '')}|${mode.name}';
  void close() => client.close();
  void checkMode(Json json) {
    if (parseMode(json['mode']) != mode) {
      throw const ApiException(
        'Le mode du serveur diffère du mode configuré. Vérifiez APP_MODE.',
        incompatible: true,
      );
    }
  }

  Future<Json> get(String path, [Map<String, String> params = const {}]) async {
    final uri = base.replace(
      path: '${base.path.replaceFirst(RegExp(r'/+$'), '')}/api/v1$path',
      queryParameters: params.isEmpty ? null : params,
    );
    try {
      final response = await client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(timeout);
      if (response.statusCode != 200) {
        throw ApiException(
          'Service indisponible (HTTP ${response.statusCode}). Réessayez.',
        );
      }
      return jsonDecode(utf8.decode(response.bodyBytes)) as Json;
    } on TimeoutException {
      throw const ApiException('Délai de réponse dépassé. Réessayez.');
    } on http.ClientException {
      throw const ApiException('Connexion au serveur impossible.');
    } on FormatException {
      throw const ApiException(
        'Réponse du serveur invalide.',
        incompatible: true,
      );
    } on TypeError {
      throw const ApiException(
        'Contrat de réponse incompatible.',
        incompatible: true,
      );
    }
  }

  Future<List<dynamic>> all(String path) async {
    final items = <dynamic>[];
    var offset = 0;
    while (true) {
      final page = await get(path, {'limit': '500', 'offset': '$offset'});
      checkMode(page);
      final batch = page['items'] as List<dynamic>;
      final total = page['total'] as int;
      if (page['offset'] != offset ||
          total < 0 ||
          batch.length > 500 ||
          (batch.isEmpty && offset < total) ||
          offset + batch.length > total) {
        throw const ApiException(
          'Pagination incohérente. Réessayez.',
          incompatible: true,
        );
      }
      items.addAll(batch);
      offset += batch.length;
      if (offset >= total) return items;
    }
  }

  Future<Json> catalog() async {
    final overview = await get('/overview');
    checkMode(overview);
    final basins = await all('/basins');
    final sources = await all('/sources');
    final payload = <String, dynamic>{
      'overview': overview,
      'basins': basins,
      'sources': sources,
    };
    Catalog.fromJson(payload);
    return payload;
  }

  Future<List<dynamic>> history(String id) async {
    final values = await all(
      '/reservoirs/${Uri.encodeComponent(id)}/measurements',
    );
    final seen = <String>{};
    for (final raw in values) {
      final measurement = Measurement.fromJson(raw as Json);
      if (!measurement.allowedIn(mode) ||
          measurement.reservoirId != id ||
          !seen.add(measurement.id)) {
        throw const ApiException(
          'Historique ou provenance incohérente.',
          incompatible: true,
        );
      }
    }
    return values;
  }
}
