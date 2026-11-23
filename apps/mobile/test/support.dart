import 'dart:convert';

import 'package:aquamaroc_mobile/data/api_client.dart';
import 'package:aquamaroc_mobile/data/local_store.dart';
import 'package:aquamaroc_mobile/data/repository.dart';
import 'package:aquamaroc_mobile/domain/models.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

// Synthetic test fixture only. No geographic or official measures.
Json measurement({
  String id = 'm1',
  String observed = '2026-01-01',
  Object? storage = '12.8',
  Object? filling = '25.6',
  String source = 's1',
  String kind = 'DEMO',
}) => {
  'id': id,
  'reservoir_id': 'r1',
  'source_id': source,
  'ingestion_run_id': 'run1',
  'observation_date': observed,
  'storage_mm3': storage,
  'filling_rate_pct': filling,
  'published_at': null,
  'ingested_at': '2026-01-03T09:00:00Z',
  'quality_status': 'valid',
  'data_kind': kind,
};
Json reservoir({
  String id = 'r1',
  String name = 'Réservoir synthétique Alpha',
}) => {
  'id': id,
  'basin_id': 'b1',
  'name': name,
  'capacity_mm3': null,
  'capacity_source': null,
  'latitude': null,
  'longitude': null,
  'coordinates_source': null,
};
Json sourceJson() => {
  'source_id': 's1',
  'title': 'Fixture DEMO',
  'producer': 'Tests synthétiques',
  'dataset_url': null,
  'license': null,
  'verification_status': 'DEMO',
  'latest_observation_date': '2026-01-02',
  'latest_published_at': null,
  'latest_ingested_at': '2026-01-03T09:00:00Z',
};
Json overview() => {
  'mode': 'demo',
  'is_real_time': false,
  'reservoirs': [
    {
      'reservoir': reservoir(),
      'basin_name': 'Bassin synthétique',
      'latest_date': '2026-01-02',
      'latest': measurement(id: 'm2', observed: '2026-01-02', storage: '13.1'),
      'source_count': 1,
    },
  ],
  'reservoir_count': 1,
  'latest_observation_date': '2026-01-02',
  'storage_mm3': '13.1',
  'weighted_filling_rate_pct': null,
  'comparable_count': 1,
  'storage_status': 'available',
  'filling_status': 'unverified_capacities',
};
Json catalogJson() => {
  'overview': overview(),
  'basins': [
    {'id': 'b1', 'name': 'Bassin synthétique'},
  ],
  'sources': [sourceJson()],
};
Json page(
  List<dynamic> items, {
  int offset = 0,
  int? total,
  String mode = 'demo',
}) => {
  'items': items,
  'mode': mode,
  'offset': offset,
  'total': total ?? items.length,
  'limit': 500,
  'is_real_time': false,
};
http.Response response(Object body, [int status = 200]) => http.Response.bytes(
  utf8.encode(jsonEncode(body)),
  status,
  headers: {'content-type': 'application/json; charset=utf-8'},
);
http.Response defaultResponse(http.Request request) =>
    switch (request.url.path) {
      '/api/v1/overview' => response(overview()),
      '/api/v1/basins' => response(
        page(catalogJson()['basins'] as List<dynamic>),
      ),
      '/api/v1/sources' => response(page([sourceJson()])),
      '/api/v1/reservoirs/r1/measurements' => response(
        page([
          measurement(),
          measurement(id: 'm2', observed: '2026-01-02', storage: '13.1'),
        ]),
      ),
      _ => response({}, 404),
    };

class MemoryStore implements LocalStore {
  final values = <String, String>{};
  bool failRead = false, failWrite = false;
  @override
  Future<String?> read(String key) async {
    if (failRead) throw StateError('Storage unavailable');
    return values[key];
  }

  @override
  Future<void> write(String key, String value) async {
    if (failWrite) throw StateError('Storage full');
    values[key] = value;
  }
}

AquaRepository repository({
  MemoryStore? store,
  http.Client? client,
  AppMode mode = AppMode.demo,
  String url = 'http://localhost:8000',
}) => AquaRepository(
  ApiClient(
    baseUrl: url,
    mode: mode,
    client: client ?? MockClient((request) async => defaultResponse(request)),
  ),
  store ?? MemoryStore(),
  now: () => DateTime.utc(2026, 1, 3, 10),
);
