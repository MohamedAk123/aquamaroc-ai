import 'dart:convert';

import 'package:aquamaroc_mobile/data/api_client.dart';
import 'package:aquamaroc_mobile/domain/models.dart';
import 'package:aquamaroc_mobile/presentation/app_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';

import 'support.dart';

void main() {
  test(
    'Catalog/history cache survive repository recreation with sync timestamp',
    () async {
      final store = MemoryStore(), repo = repository();
      final first = repository(store: store);
      await first.refreshCatalog();
      await first.history('r1');
      final second = repository(store: store);
      expect((await second.cachedCatalog())!.offline, isTrue);
      expect(
        (await second.cachedCatalog())!.syncedAt,
        DateTime.utc(2026, 1, 3, 10),
      );
      expect((await second.cachedHistory('r1'))!.value.length, 2);
      expect(await repo.cachedCatalog(), isNull);
    },
  );
  test('Mode and server isolate both cache and favorites', () async {
    final store = MemoryStore(), demo = repository();
    final repo = repository(store: store);
    await repo.refreshCatalog();
    await repo.saveFavorites({'r1'});
    for (final other in [
      repository(store: store, mode: AppMode.official),
      repository(store: store, url: 'http://other:8000'),
    ]) {
      expect(await other.cachedCatalog(), isNull);
      expect(await other.favorites(), isEmpty);
    }
    expect(await repository(store: store).favorites(), {'r1'});
    expect(await demo.favorites(), isEmpty);
  });
  test('Corrupt/foreign cache ignored; storage write failure leaves live data usable', () async {
    final store = MemoryStore(), repo = repository();
    final current = repository(store: store);
    store.values[current.key('catalog')] = '{broken';
    expect(await current.cachedCatalog(), isNull);
    store.values[current.key('catalog')] = jsonEncode({
      'version': 1,
      'namespace': 'other',
      'payload': catalogJson(),
      'synced_at': '2026-01-01',
    });
    expect(await current.cachedCatalog(), isNull);
    store.failWrite = true;
    expect((await current.refreshCatalog()).persisted, isFalse);
    expect((await repo.refreshCatalog()).value.overview.count, 1);
  });
  test('Offline startup uses existing cache with explicit failure and no invented refresh time', () async {
    final store = MemoryStore();
    await repository(store: store).refreshCatalog();
    final controller = AppController(
      repository(
        store: store,
        client: MockClient(
          (_) async => throw const ApiException('Hors connexion'),
        ),
      ),
    );
    await controller.initialize();
    expect(controller.loading, isFalse);
    expect(controller.catalog!.offline, isTrue);
    expect(controller.error, 'Hors connexion');
    expect(controller.catalog!.syncedAt, DateTime.utc(2026, 1, 3, 10));
    controller.dispose();
  });
  test('Fresh server mode mismatch invalidates cache presentation', () async {
    final store = MemoryStore();
    await repository(store: store).refreshCatalog();
    final controller = AppController(
      repository(
        store: store,
        client: MockClient(
          (_) async => response(overview()..['mode'] = 'official'),
        ),
      ),
    );
    await controller.initialize();
    expect(controller.catalog, isNull);
    expect(controller.error, contains('mode'));
    controller.dispose();
  });
  test(
    'Favorite changes persist and failed writes never claim success',
    () async {
      final store = MemoryStore(), repo = repository();
      final controller = AppController(repository(store: store));
      await controller.initialize();
      await controller.toggleFavorite('r1');
      expect(await repository(store: store).favorites(), {'r1'});
      store.failWrite = true;
      await controller.toggleFavorite('r1');
      expect(controller.favorites, {'r1'});
      expect(controller.localError, isNotNull);
      store.failWrite = false;
      await controller.toggleFavorite('r1');
      expect(await repository(store: store).favorites(), isEmpty);
      expect(await repo.favorites(), isEmpty);
      controller.dispose();
    },
  );
}
