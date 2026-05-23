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
    required XFile photo,
    XFile? referencePhoto,
    String? Function()? readCurrentNote,
    ReferenceData? Function()? readCurrentReferenceData,
    void Function(String status)? onStatus,
  }) async {
    final createdAt = DateTime.now();
    final incId = await _storage.nextIncrementForDate(
      prefix: 'Foto',
      date: createdAt,
    );
    final id = 'Foto_${dateForId(createdAt)}_$incId';
    final measurements = <GnssMeasurement>[];

    onStatus?.call('Foto wird in den Experiment-Ordner kopiert...');
    final savedPhoto = await _storage.copyImageToExperimentFolder(
      sourcePath: photo.path,
      experimentId: id,
      subfolder: 'fotos',
      fileBaseName: '${id}_foto',
    );

    SavedImageFile? savedReferencePhoto;
    if (referencePhoto != null) {
      onStatus?.call('Referenzfoto wird in den Experiment-Ordner kopiert...');
      savedReferencePhoto = await _storage.copyImageToExperimentFolder(
        sourcePath: referencePhoto.path,
        experimentId: id,
        subfolder: 'referenzfotos',
        fileBaseName: '${id}_referenzfoto',
      );
    }

    final metadata = await readExifMetadata(savedPhoto.file.path);
    final referenceMetadata = await readExifMetadata(savedReferencePhoto?.file.path);

    for (var i = 0; i < measurementOffsetsSeconds.length; i++) {
      final offset = measurementOffsetsSeconds[i];
      if (i > 0) {
        final previousOffset = measurementOffsetsSeconds[i - 1];
        await Future<void>.delayed(Duration(seconds: offset - previousOffset));
      }

      final currentNote = _cleanText(readCurrentNote?.call());
      onStatus?.call('Messung ${i + 1}/${measurementOffsetsSeconds.length} bei +${offset}s läuft...');
      final measurement = await _gnss.takeMeasurement(
        experimentId: id,
        sequenceNumber: i + 1,
        environmentType: environmentType,
        offsetSeconds: offset,
        note: currentNote,
      );
      measurements.add(measurement);
    }

    final finalNote = _cleanText(readCurrentNote?.call());
    final finalReferenceData = readCurrentReferenceData?.call();
    final normalizedMeasurements = measurements
        .map((measurement) => measurement.copyWith(note: finalNote))
        .toList(growable: false);

    final record = PhotoExperimentRecord(
      id: id,
      createdAtUtc: createdAt.toUtc(),
      environmentType: environmentType,
      note: finalNote,
      referenceData: finalReferenceData?.hasAnyValue == true ? finalReferenceData : null,
      photoPath: savedPhoto.file.path,
      photoRelativePath: savedPhoto.relativePath,
      referencePhotoPath: savedReferencePhoto?.file.path,
      referencePhotoRelativePath: savedReferencePhoto?.relativePath,
      photoMetadata: metadata,
      referencePhotoMetadata: referenceMetadata,
      measurements: normalizedMeasurements,
    );

    await _storage.saveJson(fileName: id, json: record.toJson());
    onStatus?.call('Gespeichert: $id.json');
    return record;
  }

  String? _cleanText(String? value) {
    final trimmed = value?.trim();
    if (trimmed == null || trimmed.isEmpty) return null;
    return trimmed;
  }
}
