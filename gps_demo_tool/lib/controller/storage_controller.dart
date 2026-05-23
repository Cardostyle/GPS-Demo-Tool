import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

class SavedImageFile {
  const SavedImageFile({
    required this.file,
    required this.relativePath,
  });

  final File file;
  final String relativePath;
}

class StorageController {
  static const String rootFolderName = 'gps_experiments';

  Future<Directory> experimentDirectory() async {
    Directory directory;

    if (Platform.isAndroid) {
      directory = Directory('/storage/emulated/0/Documents/$rootFolderName');
    } else {
      final base = await getApplicationDocumentsDirectory();
      directory = Directory('${base.path}/$rootFolderName');
    }

    if (!await directory.exists()) {
      await directory.create(recursive: true);
    }

    return directory;
  }

  Future<int> nextIncrementForDate({
    required String prefix,
    required DateTime date,
  }) async {
    final directory = await experimentDirectory();
    final datePart = _datePart(date);
    final matcher = RegExp('^${RegExp.escape(prefix)}_${RegExp.escape(datePart)}_(\\d+)\\.json\$');
    var highest = 0;

    await for (final entity in directory.list()) {
      if (entity is! File) continue;
      final match = matcher.firstMatch(_basename(entity.path));
      if (match == null) continue;
      final value = int.tryParse(match.group(1) ?? '');
      if (value != null && value > highest) highest = value;
    }

    return highest + 1;
  }

  Future<File> saveJson({
    required String fileName,
    required Map<String, dynamic> json,
  }) async {
    final directory = await experimentDirectory();
    final safeFileName = sanitizeFileName(fileName);
    final file = File('${directory.path}/$safeFileName.json');
    const encoder = JsonEncoder.withIndent('  ');

    return file.writeAsString(
      encoder.convert(json),
      flush: true,
    );
  }

  Future<SavedImageFile> copyImageToExperimentFolder({
    required String sourcePath,
    required String subfolder,
    required String fileBaseName,
  }) async {
    final directory = await experimentDirectory();
    final imageDirectory = Directory('${directory.path}/$subfolder');

    if (!await imageDirectory.exists()) {
      await imageDirectory.create(recursive: true);
    }

    final extension = _safeExtension(sourcePath);
    final safeBaseName = sanitizeFileName(fileBaseName);
    final targetName = '$safeBaseName$extension';
    final targetFile = File('${imageDirectory.path}/$targetName');
    final copied = await File(sourcePath).copy(targetFile.path);
    final relativePath = '$subfolder/$targetName';

    return SavedImageFile(
      file: copied,
      relativePath: relativePath,
    );
  }

  Future<List<FileSystemEntity>> listSavedExperiments() async {
    final directory = await experimentDirectory();

    if (!await directory.exists()) {
      return [];
    }

    final files = await directory
        .list()
        .where((entity) => entity.path.endsWith('.json'))
        .toList();

    files.sort((a, b) => b.path.compareTo(a.path));

    return files;
  }

  String sanitizeFileName(String value) {
    final sanitized = value
        .trim()
        .replaceAll(RegExp(r'[^A-Za-z0-9_\-]'), '_')
        .replaceAll(RegExp(r'_+'), '_');

    return sanitized.isEmpty ? 'experiment' : sanitized;
  }

  String _datePart(DateTime date) {
    final local = date.toLocal();
    final year = local.year.toString().padLeft(4, '0');
    final month = local.month.toString().padLeft(2, '0');
    final day = local.day.toString().padLeft(2, '0');
    return '$year-$month-$day';
  }

  String _safeExtension(String sourcePath) {
    final fileName = _basename(sourcePath);
    final dotIndex = fileName.lastIndexOf('.');
    if (dotIndex < 0 || dotIndex == fileName.length - 1) return '.jpg';

    final extension = fileName.substring(dotIndex).toLowerCase();
    if (extension.length > 8) return '.jpg';
    return extension;
  }

  String _basename(String path) {
    final normalized = path.replaceAll('\\', '/');
    final slashIndex = normalized.lastIndexOf('/');
    if (slashIndex < 0) return normalized;
    return normalized.substring(slashIndex + 1);
  }
}
