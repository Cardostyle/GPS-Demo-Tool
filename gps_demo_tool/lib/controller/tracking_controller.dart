import 'dart:async';

import 'experiment_models.dart';
import 'gnss_controller.dart';
import 'storage_controller.dart';

class TrackingController {
  TrackingController({
    GnssController? gnssController,
    StorageController? storageController,
  })  : _gnss = gnssController ?? GnssController(),
        _storage = storageController ?? StorageController();

  final GnssController _gnss;
  final StorageController _storage;

  Future<TrackingExperimentRecord> runTrackingExperiment({
    required int durationSeconds,
    required int intervalSeconds,
    required EnvironmentType environmentType,
    String? note,
    void Function(String status, List<GnssMeasurement> measurements)? onUpdate,
  }) async {
    if (durationSeconds <= 0) {
      throw const GnssException('Die Messdauer muss größer als 0 Sekunden sein.');
    }
    if (intervalSeconds <= 0) {
      throw const GnssException('Das Intervall muss größer als 0 Sekunden sein.');
    }

    final createdAt = DateTime.now();
    final incId = await _storage.nextIncrementForDate(
      prefix: 'Tracking',
      date: createdAt,
    );
    final id = 'Tracking_${dateForId(createdAt)}_$incId';
    final measurements = <GnssMeasurement>[];
    final count = (durationSeconds / intervalSeconds).ceil();

    for (var i = 0; i < count; i++) {
      if (i > 0) {
        await Future<void>.delayed(Duration(seconds: intervalSeconds));
      }

      final offset = i * intervalSeconds;
      onUpdate?.call('Tracking-Messung ${i + 1}/$count bei +${offset}s...', measurements);
      final measurement = await _gnss.takeMeasurement(
        experimentId: id,
        sequenceNumber: i + 1,
        environmentType: environmentType,
        offsetSeconds: offset,
        note: note,
      );
      measurements.add(measurement);
      onUpdate?.call('Letzter Punkt: ${measurement.latitude}, ${measurement.longitude}', measurements);
    }

    final record = TrackingExperimentRecord(
      id: id,
      createdAtUtc: createdAt.toUtc(),
      durationSeconds: durationSeconds,
      intervalSeconds: intervalSeconds,
      environmentType: environmentType,
      note: note,
      measurements: measurements,
    );

    await _storage.saveJson(fileName: id, json: record.toJson());
    onUpdate?.call('Gespeichert: $id.json', measurements);
    return record;
  }
}
