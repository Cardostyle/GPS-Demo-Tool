import 'dart:convert';

String dateForId(DateTime dateTime) {
  final local = dateTime.toLocal();
  final year = local.year.toString().padLeft(4, '0');
  final month = local.month.toString().padLeft(2, '0');
  final day = local.day.toString().padLeft(2, '0');
  return '$year-$month-$day';
}

String utcTimestampForFile(DateTime dateTime) =>
    dateTime.toUtc().toIso8601String().replaceAll(':', '-');

enum EnvironmentType {
  openArea('freie Fläche'),
  path('Weg'),
  underTrees('unter Bäumen');

  const EnvironmentType(this.label);
  final String label;
}

class ReferenceData {
  const ReferenceData({
    this.latitude,
    this.longitude,
    this.altitude,
  });

  final double? latitude;
  final double? longitude;
  final double? altitude;

  bool get hasAnyValue => latitude != null || longitude != null || altitude != null;

  Map<String, dynamic> toJson() => {
        'latitude': latitude,
        'longitude': longitude,
        'altitude': altitude,
      };
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
    required this.androidVersion,
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
    this.vdop,
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
  final String? androidVersion;
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
  final double? vdop;
  final String? note;

  GnssMeasurement copyWith({String? note}) {
    return GnssMeasurement(
      id: id,
      experimentId: experimentId,
      sequenceNumber: sequenceNumber,
      latitude: latitude,
      longitude: longitude,
      altitude: altitude,
      timestampUtc: timestampUtc,
      measuredAtUtc: measuredAtUtc,
      deviceModel: deviceModel,
      androidVersion: androidVersion,
      environmentType: environmentType,
      locationAccuracyMeters: locationAccuracyMeters,
      altitudeAccuracyMeters: altitudeAccuracyMeters,
      heading: heading,
      speed: speed,
      offsetSeconds: offsetSeconds,
      visibleSatellites: visibleSatellites,
      usedSatellites: usedSatellites,
      cn0DbHz: cn0DbHz,
      hdop: hdop,
      pdop: pdop,
      vdop: vdop,
      note: note ?? this.note,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'experimentId': experimentId,
        'sequenceNumber': sequenceNumber,
        'latitude': latitude,
        'longitude': longitude,
        'altitude': altitude,
        'timestampUtc': timestampUtc.toIso8601String(),
        'measuredAtUtc': measuredAtUtc.toIso8601String(),
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
        'vdop': vdop,
      };
}

class PhotoExperimentRecord {
  const PhotoExperimentRecord({
    required this.id,
    required this.createdAtUtc,
    required this.environmentType,
    required this.measurements,
    this.note,
    this.referenceData,
    this.photoPath,
    this.photoRelativePath,
    this.referencePhotoPath,
    this.referencePhotoRelativePath,
    this.photoMetadata,
    this.referencePhotoMetadata,
  });

  final String id;
  final DateTime createdAtUtc;
  final EnvironmentType environmentType;
  final String? note;
  final ReferenceData? referenceData;
  final String? photoPath;
  final String? photoRelativePath;
  final String? referencePhotoPath;
  final String? referencePhotoRelativePath;
  final Map<String, dynamic>? photoMetadata;
  final Map<String, dynamic>? referencePhotoMetadata;
  final List<GnssMeasurement> measurements;

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': 'photo_experiment',
        'createdAtUtc': createdAtUtc.toIso8601String(),
        'environmentType': environmentType.label,
        'deviceModel': measurements.isEmpty ? null : measurements.first.deviceModel,
        'androidVersion': measurements.isEmpty ? null : measurements.first.androidVersion,
        'note': note,
        'referenceData': referenceData?.toJson(),
        'photoPath': photoPath,
        'photoRelativePath': photoRelativePath,
        'referencePhotoPath': referencePhotoPath,
        'referencePhotoRelativePath': referencePhotoRelativePath,
        'photoMetadata': photoMetadata,
        'referencePhotoMetadata': referencePhotoMetadata,
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
        'deviceModel': measurements.isEmpty ? null : measurements.first.deviceModel,
        'androidVersion': measurements.isEmpty ? null : measurements.first.androidVersion,
        'note': note,
        'measurements': measurements.map((e) => e.toJson()).toList(),
      };

  String toPrettyJson() => const JsonEncoder.withIndent('  ').convert(toJson());
}
