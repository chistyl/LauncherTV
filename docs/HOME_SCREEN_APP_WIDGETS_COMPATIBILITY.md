# LauncherTV — Home Screen Third-Party App Widgets

## Goal
Add native Android App Widget hosting to the LauncherTV home screen so users can place supported third-party widgets (for example clock, weather, calendar, and media widgets) on the TV launcher.

## Compatibility is a release requirement
Target the widest practical range of Android TV / Google TV devices, while preserving existing launcher behavior. Do not assume that every TV firmware exposes the same widget framework or that every phone-oriented widget is TV-compatible.

### Compatibility strategy
- Use the platform `AppWidgetHost` / `AppWidgetManager` APIs rather than rendering a fake widget catalogue.
- Audit the project's actual `minSdkVersion`, `targetSdkVersion`, Gradle / AndroidX dependencies, and manifest before selecting implementation APIs.
- Keep the core host path on APIs available at the project's minimum supported Android API level.
- Isolate newer API calls behind SDK-version checks; never call newer APIs unconditionally.
- Detect whether the device exposes widget providers and whether a provider can be bound. If unavailable or blocked by OEM firmware, show a clear unsupported-state message and keep the launcher usable.
- Treat widget support as best-effort across OEM-customized Android TV builds; do not claim universal support where the system does not expose the required framework or permission flow.
- Do not require Google Play services for core widget hosting.

## User-facing requirements
1. Enter a home-screen edit mode and choose **Add widget**.
2. Show only providers reported by the device's Android widget manager.
3. Allow the user to select and bind a widget using the system-supported permission flow.
4. Place the widget in a dedicated home-screen widget area without changing the existing app-card layout (large cards: 4 per row; small cards: 6 per row).
5. Support widget size / span changes where the provider and host layout allow them.
6. Support remote-control focus, D-pad navigation, select, and back behavior.
7. Allow moving and removing a widget without uninstalling its provider app.
8. Persist widget IDs and placement metadata, and restore them safely after launcher restart or device reboot.
9. Handle provider removal, package update, invalid widget IDs, and failed binding without crashing.
10. Keep widgets visually separate from app cards and folders.

## TV-specific constraints
- Prefer landscape layouts and sensible minimum dimensions; respect provider-reported minimum sizes and resize modes.
- Ensure focus can enter and leave a widget predictably. Do not trap D-pad focus inside a widget.
- Some widgets are touch-first or depend on phone-sized layouts. Mark or gracefully handle providers that are unusable with a remote.
- Avoid assuming that a widget provider's preview image or configuration activity is available or TV-friendly.
- Provide a fallback empty state and a safe remove / retry path.

## Data and lifecycle
- Persist host/widget IDs and layout metadata; do not persist transient view instances.
- Allocate and delete widget IDs using the documented host lifecycle.
- Restore or revalidate widgets at startup; remove stale records safely.
- Handle configuration activities and binding results asynchronously through the correct Activity result flow for the project's Android baseline.

## Acceptance tests
- Build and install on the oldest Android API level the project officially supports and on at least one newer Android TV / Google TV version.
- Verify no-widget-provider and bind-denied cases.
- Add, configure, display, resize, move, remove, restart, and reboot with a widget.
- Test D-pad focus entry, traversal, activation, and exit.
- Verify app cards, folders, wallpaper, settings, and existing launcher navigation remain unchanged.
- Verify provider uninstall/update and widget restore failure do not crash the launcher.

## Implementation gate
Before implementation, inspect the source archive and record the real minimum / target SDK, manifest declarations, Activity structure, persistence approach, and existing home-screen layout. Do not raise minSdk or targetSdk, alter the current home layout, or replace the V1.9.1 baseline as an incidental part of this feature.
