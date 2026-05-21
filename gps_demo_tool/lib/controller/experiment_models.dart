import 'dart:convert';

String newExperimentId(String prefix) =>
    '${prefix}_${DateTime.now().toUtc().toIso8601String().replaceAll(':', '-')}';

enum EnvironmentType {
  openArea('freie Fläche'),
  path('Weg'),
  underTrees('unter Bäumen');

  const EnvironmentType(this.label);
  final String label;
}

class GnssMeasurement {
  const GnssMeasurement({
    required this.id,
    required this.experimentId,
    required this.sequenceNumber,
    required this.latitude,
    required this.longitude,
    required this.altitude,
    required this.timestampUtc,
    required this.measuredAtUtc,
    required this.deviceModel,
    required this.environmentType,
    required this.locationAccuracyMeters,
    required this.offsetSeconds,
    this.altitudeAccuracyMeters,
    this.heading,
    this.speed,
    this.visibleSatellites,
    this.usedSatellites,
    this.cn0DbHz,
    this.hdop,
    this.pdop,
    this.note,
  });

  final String id;
  final String experimentId;
  final int sequenceNumber;
  final double latitude;
  final double longitude;
  final double altitude;
  final DateTime timestampUtc;
  final DateTime measuredAtUtc;
  final String deviceModel;
  final EnvironmentType environmentType;
  final double locationAccuracyMeters;
  final double? altitudeAccuracyMeters;
  final double? heading;
  final double? speed;
  final int offsetSeconds;
  final int? visibleSatellites;
  final int? usedSatellites;
  final double? cn0DbHz;
  final double? hdop;
  final double? pdop;
  final String? note;

  Map<String, dynamic> toJson() => {
        'id': id,
        'experimentId': experimentId,
        'sequenceNumber': sequenceNumber,
        'latitude': latitude,
        'longitude': longitude,
        'altitude': altitude,
        'timestampUtc': timestampUtc.toIso8601String(),
        'measuredAtUtc': measuredAtUtc.toIso8601String(),
        'deviceModel': deviceModel,
        'environmentType': environmentType.label,
        'locationAccuracyMeters': locationAccuracyMeters,
        'altitudeAccuracyMeters': altitudeAccuracyMeters,
        'heading': heading,
        'speed': speed,
        'offsetSeconds': offsetSeconds,
        'visibleSatellites': visibleSatellites,
        'usedSatellites': usedSatellites,
        'cn0DbHz': cn0DbHz,
        'hdop': hdop,
        'pdop': pdop,
        'note': note,
      };
}

class PhotoExperimentRecord {
  const PhotoExperimentRecord({
    required this.id,
    required this.createdAtUtc,
    required this.environmentType,
    required this.measurements,
    this.note,
    this.photoPath,
    this.referencePhotoPath,
    this.photoMetadata,
  });

  final String id;
  final DateTime createdAtUtc;
  final EnvironmentType environmentType;
  final String? note;
  final String? photoPath;
  final String? referencePhotoPath;
  final Map<String, dynamic>? photoMetadata;
  final List<GnssMeasurement> measurements;

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': 'photo_experiment',
        'createdAtUtc': createdAtUtc.toIso8601String(),
        'environmentType': environmentType.label,
        'note': note,
        'photoPath': photoPath,
        'referencePhotoPath': referencePhotoPath,
        'photoMetadata': photoMetadata,
        'measurements': measurements.map((e) => e.toJson()).toList(),
      };

  String toPrettyJson() => const JsonEncoder.withIndent('  ').convert(toJson());
}

class TrackingExperimentRecord {
  const TrackingExperimentRecord({
    required this.id,
    required this.createdAtUtc,
    required this.durationSeconds,
    required this.intervalSeconds,
    required this.environmentType,
    required this.measurements,
    this.note,
  });

  final String id;
  final DateTime createdAtUtc;
  final int durationSeconds;
  final int intervalSeconds;
  final EnvironmentType environmentType;
  final String? note;
  final List<GnssMeasurement> measurements;

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': 'tracking_experiment',
        'createdAtUtc': createdAtUtc.toIso8601String(),
        'durationSeconds': durationSeconds,
        'intervalSeconds': intervalSeconds,
        'environmentType': environmentType.label,
        'note': note,
        'measurements': measurements.map((e) => e.toJson()).toList(),
      };

  String toPrettyJson() => const JsonEncoder.withIndent('  ').convert(toJson());
}
