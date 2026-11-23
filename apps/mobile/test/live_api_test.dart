import 'package:aquamaroc_mobile/data/api_client.dart';
import 'package:aquamaroc_mobile/data/repository.dart';
import 'package:aquamaroc_mobile/domain/models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'support.dart';

void main() {
  const url = String.fromEnvironment('LIVE_API_URL');
  test(
    'Live read-only catalog and history retain server provenance',
    () async {
      final api = ApiClient(
        baseUrl: url,
        mode: AppMode.demo,
        client: http.Client(),
      );
      addTearDown(api.close);
      final repo = AquaRepository(api, MemoryStore());
      final data = await repo.refreshCatalog();
      expect(data.value.overview.mode, AppMode.demo);
      expect(data.value.overview.reservoirs, isNotEmpty);
      for (final item in data.value.overview.reservoirs) {
        final history = await repo.history(item.reservoir.id);
        expect(history.value, isNotEmpty);
        expect(history.value.every((m) => m.kind == DataKind.demo), isTrue);
        expect(
          history.value.every((m) => data.value.source(m.sourceId) != null),
          isTrue,
        );
      }
    },
    skip: url.isEmpty
        ? 'Activer avec --dart-define=LIVE_API_URL=http://127.0.0.1:8000 (serveur DEMO)'
        : false,
  );
}
