import 'dart:async';

import 'package:aquamaroc_mobile/data/api_client.dart';

import 'package:aquamaroc_mobile/presentation/app.dart';
import 'package:aquamaroc_mobile/presentation/app_controller.dart';
import 'package:material_ui/material_ui.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'support.dart';

Future<void> start(
  WidgetTester tester, {
  http.Client? client,
  MemoryStore? store,
}) async {
  await tester.binding.setSurfaceSize(const Size(360, 780));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    AquaMarocApp(
      controller: AppController(repository(store: store, client: client)),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> tab(WidgetTester tester, String text) async {
  await tester.tap(find.widgetWithText(NavigationDestination, text));
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('Prévisions IA ouvre le scénario de remplissage DEMO', (
    tester,
  ) async {
    var attempts = 0;
    await start(
      tester,
      client: MockClient((request) async {
        if (!request.url.path.endsWith('/demo/forecast')) {
          return defaultResponse(request);
        }
        if (++attempts == 1) return http.Response('', 503);
        return response({
          'data_kind': 'DEMO',
          'status': 'experimental_synthetic_training',
          'target_kind': 'filling_rate_pct',
          'horizon_days': 7,
          'target_date': '2026-01-08',
          'weather': {
            'provider': 'Open-Meteo',
            'kind': 'weather_model_forecast',
            'issue_date': '2026-01-01',
            'mountain_point': 'Point de test',
          },
          'conditions': {
            'forecast_rain_mm': 0,
            'forecast_snow_water_mm': 0,
            'forecast_temperature_c': 4,
            'snow_water_mm': 12,
            'forecast_melt_mm': 10,
          },
          'reservoirs': [
            {
              'name': 'Barrage DEMO Test',
              'capacity_mm3_demo': 100,
              'initial_filling_pct_demo': 50,
              'predicted_filling_pct_demo': 52.3,
              'predicted_storage_mm3_demo': 52.3,
              'h2o_filling_pct_demo': 52.3,
            },
          ],
          'selected_on_synthetic_validation': 'h2o_automl',
          'h2o_candidate': 'modele_test',
          'mlflow_run_id': 'test',
          'metrics_synthetic_only': {
            'test_selected': {'mae_pp': 0.7},
            'test_persistence': {'mae_pp': 1.2},
          },
        });
      }),
    );
    await tester.tap(find.text('Prévisions IA'));
    await tester.pumpAndSettle();
    expect(find.textContaining('momentanément inaccessible'), findsOneWidget);
    await tester.tap(find.text('Réessayer'));
    await tester.pumpAndSettle();
    expect(
      find.textContaining('Prévisions officielles J+7 et J+30'),
      findsOneWidget,
    );
    expect(
      find.text('DEMO · Simulation à J+7 · Barrages fictifs'),
      findsOneWidget,
    );
    expect(find.text('52,30 %'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'A selected basin disappearing after refresh stays explicit without crashing',
    (tester) async {
      var removed = false;
      await start(
        tester,
        client: MockClient((request) async {
          if (removed && request.url.path.endsWith('/basins')) {
            return response(page(<dynamic>[]));
          }
          if (removed && request.url.path.endsWith('/overview')) {
            return response(
              overview()
                ..['reservoirs'] = <dynamic>[]
                ..['reservoir_count'] = 0,
            );
          }
          return defaultResponse(request);
        }),
      );
      await tab(tester, 'Barrages');
      await tester.tap(find.widgetWithText(ChoiceChip, 'Bassin synthétique'));
      await tester.pumpAndSettle();
      removed = true;
      await tester.tap(find.byTooltip('Synchroniser'));
      await tester.pumpAndSettle();
      expect(find.text('Bassin indisponible'), findsOneWidget);
      expect(find.text('Aucun barrage dans cette sélection.'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('Offline cache is visibly stale and retains its real sync time', (
    tester,
  ) async {
    final store = MemoryStore();
    await repository(store: store).refreshCatalog();
    await start(
      tester,
      store: store,
      client: MockClient(
        (_) async => throw const ApiException('Hors connexion'),
      ),
    );
    expect(find.textContaining('Cache local'), findsOneWidget);
    expect(find.textContaining('03/01/2026'), findsWidgets);
    expect(find.text('13,1 Mm³'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('Home and list expose accessible touch targets and contrast', (
    tester,
  ) async {
    final semantics = tester.ensureSemantics();
    await start(tester);
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));
    await tab(tester, 'Barrages');
    await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
    await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
    await expectLater(tester, meetsGuideline(textContrastGuideline));
    semantics.dispose();
  });
  testWidgets(
    'Home, search, favorites and detail use typed API data on 360px',
    (tester) async {
      final store = MemoryStore();
      await start(tester, store: store);
      expect(
        find.text('DEMO · Données synthétiques · Aucun barrage réel'),
        findsOneWidget,
      );
      expect(find.text('13,1 Mm³'), findsOneWidget);
      expect(find.text('Non disponible'), findsOneWidget);
      await tab(tester, 'Barrages');
      await tester.enterText(find.byType(TextField), 'absent');
      await tester.pumpAndSettle();
      expect(find.text('Aucun barrage dans cette sélection.'), findsOneWidget);
      await tester.tap(find.byTooltip('Effacer la recherche'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byTooltip('Ajouter aux favoris'));
      await tester.tap(find.byTooltip('Ajouter aux favoris'));
      await tester.pumpAndSettle();
      expect(await repository(store: store).favorites(), {'r1'});
      await tab(tester, 'Favoris');
      expect(find.text('Réservoir synthétique Alpha'), findsOneWidget);
      await tester.tap(find.text('Réservoir synthétique Alpha'));
      await tester.pumpAndSettle();
      expect(find.text('Détail barrage'), findsOneWidget);
      await tester.ensureVisible(find.text('Historique'));
      await tester.tap(find.text('Historique'));
      await tester.pumpAndSettle();
      await tester.scrollUntilVisible(
        find.text('Relevés et provenance (2)'),
        350,
        scrollable: find.byType(Scrollable).first,
      );
      expect(find.text('Relevés et provenance (2)'), findsOneWidget);
      expect(tester.takeException(), isNull);
    },
  );
  testWidgets('Map empty state and data provenance stay explicit', (
    tester,
  ) async {
    await start(tester);
    await tab(tester, 'Carte');
    final map = tester.widget<FlutterMap>(find.byType(FlutterMap));
    expect(
      tester.widget<MarkerLayer>(find.byType(MarkerLayer)).markers,
      isEmpty,
    );
    await tester.tap(find.byTooltip('Zoom avant'));
    await tester.pumpAndSettle();
    expect(map.mapController!.camera.zoom, 7);
    await tester.tap(find.byTooltip('Recentrer la carte'));
    await tester.pumpAndSettle();
    expect(map.mapController!.camera.zoom, 6);
    expect(
      find.textContaining('Coordonnées vérifiées non disponibles'),
      findsOneWidget,
    );
    await tab(tester, 'Données');
    expect(find.text('Comment lire les données ?'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Fixture DEMO'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Fixture DEMO'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'Initial network failure offers retry without synthetic fallback',
    (tester) async {
      var failing = true;
      await start(
        tester,
        client: MockClient(
          (r) async => failing ? response({}, 503) : defaultResponse(r),
        ),
      );
      expect(find.textContaining('503'), findsOneWidget);
      expect(find.text('13,1 Mm³'), findsNothing);
      failing = false;
      await tester.tap(find.text('Réessayer'));
      await tester.pumpAndSettle();
      expect(find.text('13,1 Mm³'), findsOneWidget);
    },
  );
  testWidgets('Loading is announced before API answers', (tester) async {
    final pending = Completer<http.Response>();
    await tester.pumpWidget(
      AquaMarocApp(
        controller: AppController(
          repository(
            client: MockClient(
              (r) => r.url.path.endsWith('/overview')
                  ? pending.future
                  : Future.value(defaultResponse(r)),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    expect(find.text('Chargement des données…'), findsOneWidget);
    pending.complete(response(overview()));
    await tester.pumpAndSettle();
    expect(find.text('13,1 Mm³'), findsOneWidget);
  });
  testWidgets('Large text does not overflow on home and list', (tester) async {
    await tester.binding.setSurfaceSize(const Size(360, 780));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.8)),
        child: AquaMarocApp(controller: AppController(repository())),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    await tab(tester, 'Barrages');
    expect(tester.takeException(), isNull);
  });
  testWidgets('No data renders explicit empty states', (tester) async {
    await start(
      tester,
      client: MockClient(
        (r) async => r.url.path.endsWith('/overview')
            ? response(
                overview()
                  ..['reservoirs'] = <dynamic>[]
                  ..['reservoir_count'] = 0
                  ..['storage_mm3'] = null
                  ..['latest_observation_date'] = null
                  ..['storage_status'] = 'no_data',
              )
            : defaultResponse(r),
      ),
    );
    await tab(tester, 'Barrages');
    expect(find.text('Aucun barrage dans cette sélection.'), findsOneWidget);
    await tab(tester, 'Favoris');
    expect(find.textContaining('Aucun favori'), findsOneWidget);
  });
}
