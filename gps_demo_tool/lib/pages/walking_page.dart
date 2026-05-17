import 'package:flutter/material.dart';
import 'package:gps_demo_tool/controller/walking.dart';

class WalkingPage extends StatefulWidget {
  const WalkingPage({super.key});

  @override
  State<WalkingPage> createState() => _WalkingPageState();
}

class _WalkingPageState extends State<WalkingPage> {
  final controller = WalkingController();

  String resultText = 'Noch keine Position abgerufen.';
  bool isLoading = false;

  Future<void> getCurrentLocation() async {
    setState(() {
      isLoading = true;
    });

    final locationText = await controller.getCurrentLocationText();

    if (!mounted) return;

    setState(() {
      resultText = locationText;
      isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Laufen-Seite'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                resultText,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 20),
              ),
              const SizedBox(height: 30),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
                onPressed: isLoading ? null : getCurrentLocation,
                child: Text(isLoading ? 'Lädt...' : 'GPS-Position abrufen'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
