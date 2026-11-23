import 'dart:convert';

import '../domain/models.dart';
import 'api_client.dart';
import 'local_store.dart';

class AquaRepository {
  final ApiClient api;
  final LocalStore store;
  final DateTime Function() now;
  AquaRepository(this.api, this.store, {DateTime Function()? now})
    : now = now ?? DateTime.now;
  String key(String part) => 'aquamaroc.v1|${api.namespace}|$part';
  Future<Cached<T>?> cached<T>(String part, T Function(dynamic) decode) async {
    try {
      final raw = await store.read(key(part));
      if (raw == null) return null;
      final json = jsonDecode(raw) as Json;
      if (json['namespace'] != api.namespace || json['version'] != 1) {
        return null;
      }
      return Cached(
        decode(json['payload']),
        DateTime.parse(json['synced_at'] as String),
        offline: true,
      );
    } catch (_) {
      return null;
    } // Corrupt/unsupported caches are ignored, never synthesized.
  }

  Future<bool> save(String part, Object payload, DateTime syncedAt) async {
    try {
      await store.write(
        key(part),
        jsonEncode({
          'version': 1,
          'namespace': api.namespace,
          'synced_at': syncedAt.toUtc().toIso8601String(),
          'payload': payload,
        }),
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<Cached<Catalog>?> cachedCatalog() => cached('catalog', (raw) {
    final value = Catalog.fromJson(raw as Json);
    if (value.overview.mode != api.mode) {
      throw const FormatException('Mode du cache incompatible');
    }
    return value;
  });
  Future<Cached<Catalog>> refreshCatalog() async {
    final raw = await api.catalog();
    final value = Catalog.fromJson(raw);
    final at = now().toUtc();
    final persisted = await save('catalog', raw, at);
    return Cached(value, at, persisted: persisted);
  }

  List<Measurement> decodeHistory(dynamic raw, String id) {
    final values = (raw as List<dynamic>)
        .map((e) => Measurement.fromJson(e as Json))
        .toList();
    if (values.any((m) => !m.allowedIn(api.mode) || m.reservoirId != id)) {
      throw const FormatException('Historique du cache incompatible');
    }
    values.sort((a, b) => a.observedAt.compareTo(b.observedAt));
    return values;
  }

  Future<Cached<List<Measurement>>?> cachedHistory(String id) =>
      cached('history:$id', (raw) => decodeHistory(raw, id));
  Future<Cached<List<Measurement>>> history(String id) async {
    final raw = await api.history(id);
    final value = decodeHistory(raw, id);
    final at = now().toUtc();
    return Cached(value, at, persisted: await save('history:$id', raw, at));
  }

  Future<Set<String>> favorites() async {
    final raw = await store.read(key('favorites'));
    if (raw == null) return {};
    try {
      return (jsonDecode(raw) as List<dynamic>).cast<String>().toSet();
    } on FormatException {
      return {};
    } on TypeError {
      return {};
    }
  }

  Future<void> saveFavorites(Set<String> values) =>
      store.write(key('favorites'), jsonEncode(values.toList()..sort()));
}
