# Android TV App Widget Compatibility Matrix

This matrix defines the validation policy for LauncherTV's third-party widget host. It is intentionally capability-based: Android version alone does not guarantee that an OEM TV firmware exposes a usable widget host / provider / binding flow.

## Compatibility tiers

| Tier | Device capability | Launcher behavior | Release status |
|---|---|---|---|
| A — Full | Android widget framework present; providers enumerate; bind/configure flow succeeds; remote navigation works | Add, display, configure, resize where supported, move, remove, restore | Supported |
| B — Limited | Framework exists, but provider UI, resize, configuration activity, or D-pad behavior is limited | Display where possible; disable unsupported operations; show provider-specific limitation | Best effort |
| C — Host unavailable | Widget manager / host binding unavailable or OEM blocks required flow | Hide or disable Add widget with a clear explanation; all other launcher features remain available | Graceful fallback |
| D — Provider incompatible | Provider is missing, invalid, phone-only, touch-dependent, or fails to create a RemoteViews hierarchy | Skip or quarantine that provider; allow removal/retry; do not crash launcher | Graceful fallback |

## Android API compatibility policy

- Determine the actual `minSdkVersion` from the V1.9.1 source before implementation. Do not guess it or raise it as a shortcut.
- Use the classic `AppWidgetHost`, `AppWidgetManager`, and `RemoteViews` lifecycle supported by the project's minimum API.
- Guard newer widget sizing, preview, responsive layout, and activity-result APIs with SDK checks and fallbacks.
- Do not rely on Google Play services, a specific launcher package, or a specific OEM's widget picker.
- Treat provider-reported minimum dimensions and resize modes as hints to the host layout; do not assume all providers support resizing.
- A provider being installed does not guarantee its widget is TV-usable.
- Do not attempt to bypass OEM security, hidden API restrictions, or system binding permissions.

## Device test matrix

Test on physical devices or representative emulator images for each Android API level that the project officially claims to support:

| Test class | Required checks |
|---|---|
| Oldest supported API | Launcher starts; widget menu safely detects framework; add/display/remove if available |
| Intermediate API | Bind and configuration flows; persisted IDs; process restart restore |
| Newest supported API | Same core flows; API-guarded optional features; no deprecated API crash |
| Google TV / Android TV reference device | D-pad focus, widget interaction, provider list, landscape sizing |
| OEM-customized TV firmware | Framework availability, permission flow, app lifecycle, reboot restore |
| No widget provider installed | Empty state; no crash; normal launcher remains usable |
| Binding denied / canceled | Clear message; no orphaned widget ID |
| Provider removed / updated | Stale ID cleanup; no crash |
| Provider crashes or returns invalid views | Isolate failure; remove/retry path; launcher remains usable |

## Required functional regression

Every widget build must also verify that the existing launcher behavior is unchanged:
- Large app cards remain 4 per row.
- Small app cards remain 6 per row.
- App discovery and launching still work.
- Existing folders, wallpaper, settings, and D-pad navigation still work.
- Widget storage does not overwrite or reset existing launcher preferences.

## Release gates

1. Source audit records minSdk, targetSdk, compileSdk, manifest declarations, and Gradle / AndroidX versions.
2. CI debug build succeeds without raising minSdk.
3. Static checks confirm newer APIs are guarded.
4. Device tests cover the oldest officially supported API and a newer Android TV / Google TV device.
5. No-widget and bind-denied cases pass.
6. Widget add/configure/resize/move/remove/restore cases pass where the device supports them.
7. Regression tests confirm the original launcher remains usable when widget hosting is unavailable.

## Explicit limitation

No implementation can guarantee third-party widget support on every Android TV device. OEM firmware may omit or restrict widget hosting, and individual providers may be designed only for touch devices. LauncherTV must detect and explain these cases rather than claiming universal compatibility.
