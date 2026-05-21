import 'dart:async';

import 'package:image_picker/image_picker.dart';
import 'package:native_exif/native_exif.dart';

import 'experiment_models.dart';
import 'gnss_controller.dart';
import 'storage_controller.dart';

class PhotoExperimentController {
  PhotoExperimentController({
    GnssController? gnssController,
    StorageController? storageController,
    ImagePicker? imagePicker,
  })  : _gnss = gnssController ?? GnssController(),
        _storage = storageController ?? StorageController(),
        _picker = imagePicker ?? ImagePicker();

  static const List<int> measurementOffsetsSeconds = [0, 10, 30, 60, 120];

  final GnssController _gnss;
  final StorageController _storage;
  final ImagePicker _picker;

  Future<XFile?> takePhoto() {
    return _picker.pickImage(
      source: ImageSource.camera,
      preferredCameraDevice: CameraDevice.rear,
      imageQuality: 95,
    );
  }

  Future<Map<String, dynamic>?> readExifMetadata(String? imagePath) async {
    if (imagePath == null) return null;

    final exif = await Exif.fromPath(imagePath);
    try {
      final attributes = await exif.getAttributes();
      final originalDate = await exif.getOriginalDate();
      final latLong = await exif.getLatLong();

      return {
        'attributes': attributes?.map((key, value) => MapEntry(key, '$value')),
        'originalDate': originalDate?.toUtc().toIso8601String(),
        'latLong': latLong == null
            ? null
            : {
                'latitude': latLong.latitude,
                'longitude': latLong.longitude,
              },
      };
    } finally {
      await exif.close();
    }
  }

  Future<PhotoExperimentRecord> runPhotoExperiment({
    required EnvironmentType environmentType,
    required bool keepImageFile,
    String? note,
    XFile? photo,
    XFile? referencePhoto,
    void Function(String status)? onStatus,
  }) async {
    final id = newExperimentId('photo');
    final createdAt = DateTime.now().toUtc();
    final imagePath = photo?.path;
    final metadata = await readExifMetadata(imagePath);
    final measurements = <GnssMeasurement>[];

    for (var i = 0; i < measurementOffsetsSeconds.length; i++) {
      final offset = measurementOffsetsSeconds[i];
      if (i > 0) {
        final previousOffset = measurementOffsetsSeconds[i - 1];
        await Future<void>.delayed(Duration(seconds: offset - previousOffset));
      }

      onStatus?.call('Messung ${i + 1}/${measurementOffsetsSeconds.length} bei +${offset}s läuft...');
      final measurement = await _gnss.takeMeasurement(
        experimentId: id,
        sequenceNumber: i + 1,
        environmentType: environmentType,
        offsetSeconds: offset,
        note: note,
      );
      measurements.add(measurement);
    }

    final record = PhotoExperimentRecord(
      id: id,
      createdAtUtc: createdAt,
      environmentType: environmentType,
      note: note,
      photoPath: keepImageFile ? imagePath : null,
      referencePhotoPath: referencePhoto?.path,
      photoMetadata: metadata,
      measurements: measurements,
    );

    await _storage.saveJson(fileName: id, json: record.toJson());
    onStatus?.call('Gespeichert: $id.json');
    return record;
  }
}
