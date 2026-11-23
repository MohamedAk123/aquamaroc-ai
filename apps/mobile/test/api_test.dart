import 'dart:async';

import 'package:aquamaroc_mobile/data/api_client.dart';
import 'package:aquamaroc_mobile/domain/models.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:http/http.dart' as http;

import 'support.dart';

void main() {
  test('Catalog parses real API shape and history keeps provenance', () async {
    final repo = repository();
    final catalog = await repo.refreshCatalog();
    expect(catalog.value.overview.count, 1);
    expect(catalog.value.sources.single.title, 'Fixture DEMO');
    expect((await repo.history('r1')).value.length, 2);
  });
  test(
    'Pagination retrieves beyond first 500 items without truncation',
    () async {
      final offsets = <String>[];
      final api = ApiClient(
        baseUrl: 'http://localhost:8000/',
        mode: AppMode.demo,
        client: MockClient((r) async {
          expect(r.url.path, '/api/v1/basins');
          expect(r.url.queryParameters['limit'], '500');
          final offset = int.parse(r.url.queryParameters['offset']!);
          offsets.add('$offset');
          return response(
            page(
              List.generate(
                offset == 0 ? 500 : 1,
                (i) => {'id': '${offset + i}', 'name': 'DEMO'},
              ),
              total: 501,
              offset: offset,
            ),
          );
        }),
      );
      expect((await api.all('/basins')).length, 501);
      expect(offsets, ['0', '500']);
    },
  );
  test('Pagination cannot loop on an empty or incorrect page', () async {
    final api = repository(
      client: MockClient((_) async => response(page([], total: 20))),
    ).api;
    await expectLater(api.all('/basins'), throwsA(isA<ApiException>()));
  });
  test('Mismatched server mode is rejected', () async {
    final api = repository(
      client: MockClient(
        (_) async => response(overview()..['mode'] = 'official'),
      ),
    ).api;
    await expectLater(
      api.catalog(),
      throwsA(
        isA<ApiException>().having((e) => e.incompatible, 'incompatible', true),
      ),
    );
  });
  test('DEMO measurements cannot enter official history', () async {
    final api = repository(
      mode: AppMode.official,
      client: MockClient(
        (_) async => response(page([measurement()], mode: 'official')),
      ),
    ).api;
    await expectLater(api.history('r1'), throwsA(isA<ApiException>()));
  });
  test('Wrong reservoir and duplicate measurement ids are rejected', () async {
    for (final items in [
      [measurement()..['reservoir_id'] = 'other'],
      [measurement(), measurement()],
    ]) {
      final api = repository(
        client: MockClient((_) async => response(page(items))),
      ).api;
      await expectLater(api.history('r1'), throwsA(isA<ApiException>()));
    }
  });
  test(
    'HTTP failure, malformed JSON and timeout produce useful errors',
    () async {
      await expectLater(
        repository(client: MockClient((_) async => response({}, 503))).api
            .get('/overview'),
        throwsA(
          isA<ApiException>().having((e) => e.message, 'HTTP', contains('503')),
        ),
      );
      await expectLater(
        repository(
          client: MockClient((_) async => http.Response('not-json', 200)),
        ).api.get('/overview'),
        throwsA(isA<ApiException>()),
      );
      final api = ApiClient(
        baseUrl: 'http://localhost',
        mode: AppMode.demo,
        timeout: const Duration(milliseconds: 1),
        client: MockClient((_) => Completer<http.Response>().future),
      );
      await expectLater(
        api.get('/overview'),
        throwsA(
          isA<ApiException>().having(
            (e) => e.message,
            'timeout',
            contains('Délai'),
          ),
        ),
      );
    },
  );
  test('API URL rejects credentials and invalid schemes', () {
    for (final url in [
      'file:///local',
      'http://user:password@localhost',
      'http://localhost?secret=x',
    ]) {
      expect(() => repository(url: url), throwsFormatException);
    }
  });
}
