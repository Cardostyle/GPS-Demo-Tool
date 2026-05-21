import 'package:flutter/material.dart';

import 'package:gps_demo_tool/controller/exporting.dart';

class TrackingPage extends StatefulWidget {
  const TrackingPage({super.key});

  @override
  State<TrackingPage> createState() => _TrackingPageState();
}

class _TrackingPageState extends State<TrackingPage> {
  final controller = TrackingController();
  final durationController = TextEditingController(text: '30');
  final intervalController = TextEditingController(text: '1');
  final noteController = TextEditingController();

  EnvironmentType environmentType = EnvironmentType.path;
  bool isRunning = false;
  String status = 'Noch kein Tracking gestartet.';
  List<GnssMeasurement> measurements = const [];

  Future<void> startTracking() async {
    final duration = int.tryParse(durationController.text.trim()) ?? 30;
    final interval = int.tryParse(intervalController.text.trim()) ?? 1;

    setState(() {
      isRunning = true;
      status = 'Tracking wird vorbereitet...';
      measurements = const [];
    });

    try {
      final record = await controller.runTrackingExperiment(
        durationSeconds: duration,
        intervalSeconds: interval,
        environmentType: environmentType,
        note: noteController.text.trim().isEmpty ? null : noteController.text.trim(),
        onUpdate: (value, points) {
          if (!mounted) return;
          setState(() {
            status = value;
            measurements = List<GnssMeasurement>.from(points);
          });
        },
      );

      if (!mounted) return;
      setState(() {
        measurements = record.measurements;
        status = 'Fertig. ${record.measurements.length} Tracking-Punkte gespeichert.';
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => status = 'Fehler: $error');
    } finally {
      if (mounted) {
        setState(() => isRunning = false);
      }
    }
  }

  @override
  void dispose() {
    durationController.dispose();
    intervalController.dispose();
    noteController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tracking-Modus')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              DropdownButtonFormField<EnvironmentType>(
                value: environmentType,
                decoration: const InputDecoration(
                  labelText: 'Umgebungstyp',
                  border: OutlineInputBorder(),
                ),
                items: EnvironmentType.values
                    .map(
                      (type) => DropdownMenuItem(
                        value: type,
                        child: Text(type.label),
                      ),
                    )
                    .toList(),
                onChanged: isRunning
                    ? null
                    : (value) {
                        if (value != null) setState(() => environmentType = value);
                      },
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: durationController,
                      enabled: !isRunning,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Dauer (s)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: intervalController,
                      enabled: !isRunning,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Intervall (s)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteController,
                enabled: !isRunning,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Bemerkungen / Notizen',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: isRunning ? null : startTracking,
                icon: const Icon(Icons.directions_walk),
                label: const Text('Tracking starten'),
              ),
              const SizedBox(height: 20),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(status),
                ),
              ),
              const SizedBox(height: 12),
              Text('Erfasste Punkte: ${measurements.length}'),
              const SizedBox(height: 8),
              ...measurements.take(5).map(
                    (point) => Text(
                      '#${point.sequenceNumber}: ${point.latitude.toStringAsFixed(6)}, '
                      '${point.longitude.toStringAsFixed(6)} | '
                      '${point.locationAccuracyMeters.toStringAsFixed(1)} m',
                    ),
                  ),
              if (measurements.length > 5) const Text('...'),
            ],
          ),
        ),
      ),
    );
  }
}
