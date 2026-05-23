import 'package:flutter/material.dart';
import 'package:gps_demo_tool/pages/gnss_testing_page.dart';
import 'package:gps_demo_tool/pages/photo_experiment_page.dart';
import 'package:gps_demo_tool/pages/tracking_page.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('GPS Demo Tool'),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (context) => const PhotoExperimentPage(),
                    ),
                  );
                },
                child: const Text('Foto-Experiment'),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (context) => const TrackingPage(),
                    ),
                  );
                },
                child: const Text('Tracking-Modus'),
              ),
              const SizedBox(height: 16),
              OutlinedButton(
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(double.infinity, 50),
                ),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute<void>(
                      builder: (context) => const GnssTestingPage(),
                    ),
                  );
                },
                child: const Text('GNSS Testing'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
