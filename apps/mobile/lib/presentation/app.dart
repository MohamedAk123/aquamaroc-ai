import 'package:material_ui/material_ui.dart';

import '../domain/models.dart';
import 'app_controller.dart';
import 'widgets.dart';
import '../features/home/home_screen.dart';
import '../features/reservoirs/list_screen.dart';
import '../features/reservoirs/detail_screen.dart';
import '../features/map/map_screen.dart';
import '../features/sources/sources_screen.dart';
import '../features/variations/variation_screen.dart';
import '../features/forecasts/forecast_screen.dart';

class AquaMarocApp extends StatefulWidget {
  final AppController controller;
  const AquaMarocApp({super.key, required this.controller});
  @override
  State<AquaMarocApp> createState() => _AquaMarocAppState();
}

class _AquaMarocAppState extends State<AquaMarocApp> {
  @override
  void initState() {
    super.initState();
    widget.controller.initialize();
  }

  @override
  void dispose() {
    widget.controller.repository.api.close();
    widget.controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'AquaMaroc AI',
    debugShowCheckedModeBanner: false,
    locale: const Locale('fr'),
    supportedLocales: const [Locale('fr')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: water,
        primary: water,
        onPrimary: Colors.white,
        onSurface: const Color(0xff0d1b30),
      ),
      scaffoldBackgroundColor: const Color(0xffeef6fc),
      appBarTheme: const AppBarTheme(
        backgroundColor: Color(0xffe4f2fc),
        foregroundColor: Color(0xff0d1b30),
      ),
      cardTheme: CardThemeData(
        elevation: 2,
        shadowColor: const Color(0x24365d7c),
        color: Colors.white,
        margin: const EdgeInsets.symmetric(vertical: 6),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0xffd6e4f2)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.white,
      ),
    ),
    home: MobileShell(controller: widget.controller),
  );
}

class MobileShell extends StatefulWidget {
  final AppController controller;
  const MobileShell({super.key, required this.controller});
  @override
  State<MobileShell> createState() => _MobileShellState();
}

class _MobileShellState extends State<MobileShell> {
  int tab = 0;
  static const titles = ['Accueil', 'Barrages', 'Carte', 'Favoris', 'Données'];
  void open(Snapshot item) {
    final data = widget.controller.catalog!;
    Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => DetailScreen(
          item: item,
          controller: widget.controller,
          catalog: data.value,
          catalogSyncedAt: data.syncedAt,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: widget.controller,
    builder: (context, _) {
      final controller = widget.controller;
      final data = controller.catalog;
      Widget content;
      if (data == null) {
        content = Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: controller.loading
                ? const Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Chargement des données…'),
                    ],
                  )
                : Notice(
                    controller.error ?? 'Aucune donnée disponible.',
                    warning: true,
                    action: TextButton(
                      onPressed: controller.refresh,
                      child: const Text('Réessayer'),
                    ),
                  ),
          ),
        );
      } else if (tab == 2) {
        content = Padding(
          padding: const EdgeInsets.all(16),
          child: MapScreen(catalog: data.value, onOpen: open),
        );
      } else {
        final catalog = data.value;
        content = RefreshIndicator(
          onRefresh: controller.refresh,
          child: ListView(
            key: PageStorageKey('tab-$tab'),
            padding: const EdgeInsets.all(16),
            physics: const AlwaysScrollableScrollPhysics(),
            children: [
              if (tab != 0)
                Text(
                  titles[tab],
                  style: Theme.of(context).textTheme.headlineMedium
                      ?.copyWith(fontWeight: FontWeight.bold, color: navy),
                ),
              if (tab != 0 || data.offline || !data.persisted) SyncNotice(data),
              if (controller.error != null)
                Notice(controller.error!, warning: true),
              if (controller.localError != null)
                Notice(controller.localError!, warning: true),
              if (controller.loading)
                const LinearProgressIndicator(
                  semanticsLabel: 'Synchronisation en cours',
                ),
              const SizedBox(height: 8),
              switch (tab) {
                0 => HomeScreen(
                  catalog: catalog,
                  controller: controller,
                  onOpen: open,
                  onBrowse: () => setState(() => tab = 1),
                  onMap: () => setState(() => tab = 2),
                  onFavorites: () => setState(() => tab = 3),
                  onSources: () => setState(() => tab = 4),
                  onVariations: () => Navigator.of(context).push<void>(
                    MaterialPageRoute(
                      builder: (_) =>
                          VariationScreen(api: controller.repository.api),
                    ),
                  ),
                  onForecasts: () => Navigator.of(context).push<void>(
                    MaterialPageRoute(
                      builder: (_) =>
                          ForecastScreen(api: controller.repository.api),
                    ),
                  ),
                  syncedAt: data.syncedAt,
                ),
                1 => ReservoirListScreen(
                  key: const ValueKey('all'),
                  catalog: catalog,
                  controller: controller,
                  onOpen: open,
                ),
                3 => ReservoirListScreen(
                  key: const ValueKey('favorites'),
                  catalog: catalog,
                  controller: controller,
                  onOpen: open,
                  favoritesOnly: true,
                ),
                _ => SourcesScreen(catalog: catalog),
              },
              const SizedBox(height: 20),
              const Text(
                'Projet indépendant · Aucune communication officielle des autorités hydrauliques.',
                style: TextStyle(fontSize: 12),
              ),
            ],
          ),
        );
      }
      final mode = controller.repository.api.mode;
      return Scaffold(
        appBar: AppBar(
          title: const Row(
            children: [
              Icon(Icons.water_drop, color: water),
              SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AquaMaroc AI',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    Text(
                      'Suivi des barrages du Maroc',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 11),
                    ),
                  ],
                ),
              ),
            ],
          ),
          actions: [
            IconButton(
              tooltip: 'Synchroniser',
              onPressed: controller.loading ? null : controller.refresh,
              icon: const Icon(Icons.sync),
            ),
          ],
        ),
        body: SafeArea(
          child: Column(
            children: [
              Container(
                width: double.infinity,
                color: mode == AppMode.demo
                    ? const Color(0xffffefce)
                    : const Color(0xffe9f5fc),
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
                child: Text(
                  mode == AppMode.demo
                      ? 'DEMO · Données synthétiques · Aucun barrage réel'
                      : 'Mode officiel · Vérifiez la provenance de chaque relevé',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: navy,
                  ),
                ),
              ),
              Expanded(child: content),
            ],
          ),
        ),
        bottomNavigationBar: NavigationBar(
          backgroundColor: const Color(0xfff7fbff),
          indicatorColor: const Color(0xffcfeefa),
          selectedIndex: tab,
          onDestinationSelected: (value) => setState(() => tab = value),
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'Accueil',
            ),
            NavigationDestination(
              icon: Icon(Icons.bar_chart),
              label: 'Barrages',
            ),
            NavigationDestination(
              icon: Icon(Icons.map_outlined),
              label: 'Carte',
            ),
            NavigationDestination(
              icon: Icon(Icons.favorite_border),
              label: 'Favoris',
            ),
            NavigationDestination(
              icon: Icon(Icons.info_outline),
              label: 'Données',
            ),
          ],
        ),
      );
    },
  );
}
