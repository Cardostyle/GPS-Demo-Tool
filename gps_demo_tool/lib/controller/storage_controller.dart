import 'dart:convert';
import 'dart:io';

import 'package:path_provider/path_provider.dart';

class StorageController {
  Future<Directory> experimentDirectory() async {
    Directory directory;

    if (Platform.isAndroid) {
      // Öffentlicher Documents-Ordner auf Android
      directory = Directory('/storage/emulated/0/Documents/gps_experiments');
    } else {
      // Fallback für andere Plattformen
      final base = await getApplicationDocumentsDirectory();
      directory = Directory('${base.path}/gps_experiments');
    }

    if (!await directory.exists()) {
      await directory.create(recursive: true);
    }

    return directory;
  }

  Future<File> saveJson({
    required String fileName,
    required Map<String, dynamic> json,
  }) async {
    final directory = await experimentDirectory();

    final safeFileName = fileName
        .replaceAll(RegExp(r'[^\w\-]'), '_')
        .replaceAll('__', '_');

    final file = File('${directory.path}/$safeFileName.json');

    const encoder = JsonEncoder.withIndent('  ');

    return file.writeAsString(
      encoder.convert(json),
      flush: true,
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
}