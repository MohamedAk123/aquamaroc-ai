import 'package:flutter/foundation.dart';

import '../data/api_client.dart';
import '../data/repository.dart';
import '../domain/models.dart';

class AppController extends ChangeNotifier {
  final AquaRepository repository;
  Cached<Catalog>? catalog;
  Set<String> favorites = {};
  bool loading = true, savingFavorite = false;
  String? error, localError;
  bool _disposed = false;
  bool _refreshing = false;
  AppController(this.repository);
  void changed() {
    if (!_disposed) notifyListeners();
  }

  Future<void> initialize() async {
    catalog = await repository.cachedCatalog();
    try {
      favorites = await repository.favorites();
    } catch (_) {
      localError = 'Les favoris locaux ne sont pas accessibles.';
    }
    changed();
    await refresh();
  }

  Future<void> refresh() async {
    if (_refreshing || _disposed) return;
    _refreshing = true;
    loading = true;
    error = null;
    changed();
    try {
      catalog = await repository.refreshCatalog();
    } catch (e) {
      error = e is ApiException
          ? e.message
          : 'Les données reçues ne peuvent pas être lues.';
      // A server mode/contract mismatch must never expose a previous catalog.
      if ((e is ApiException && e.incompatible) ||
          e is FormatException ||
          e is TypeError) {
        catalog = null;
      } else if (catalog != null) {
        catalog = Cached(
          catalog!.value,
          catalog!.syncedAt,
          offline: true,
          persisted: catalog!.persisted,
        );
      }
    } finally {
      _refreshing = false;
      loading = false;
      changed();
    }
  }

  Future<void> toggleFavorite(String id) async {
    if (savingFavorite) return;
    savingFavorite = true;
    localError = null;
    changed();
    final next = {...favorites};
    if (!next.add(id)) next.remove(id);
    try {
      await repository.saveFavorites(next);
      favorites = next;
    } catch (_) {
      localError = 'Enregistrement du favori impossible. Réessayez.';
    } finally {
      savingFavorite = false;
      changed();
    }
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }
}
