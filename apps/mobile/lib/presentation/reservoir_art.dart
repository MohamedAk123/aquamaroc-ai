import 'package:material_ui/material_ui.dart';

class ReservoirArt extends StatelessWidget {
  final BoxFit fit;
  const ReservoirArt({super.key, this.fit = BoxFit.cover});

  @override
  Widget build(BuildContext context) => ExcludeSemantics(
    child: Image.asset(
      'assets/reservoir-illustration.jpg',
      fit: fit,
      width: double.infinity,
      height: double.infinity,
    ),
  );
}

class ReservoirBanner extends StatelessWidget {
  final Widget? child;
  const ReservoirBanner({super.key, this.child});

  @override
  Widget build(BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(22),
    child: Stack(
      children: [
        const Positioned.fill(child: ReservoirArt()),
        const Positioned.fill(
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topRight,
                end: Alignment.bottomLeft,
                colors: [Color(0x10062237), Color(0xe0062237)],
              ),
            ),
          ),
        ),
        Container(
          width: double.infinity,
          constraints: const BoxConstraints(minHeight: 170),
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'PAYSAGE ILLUSTRATIF',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1,
                ),
              ),
              if (child != null) ...[const SizedBox(height: 20), child!],
            ],
          ),
        ),
      ],
    ),
  );
}
