# Google TV Streamer profile

This profile comes from a Google TV Streamer running Android 14 in November
2026. ADB package disables, Projectivy Home, Settings, Netflix and YouTube
launches, three animation settings, and restart persistence were checked.
Playback, casting from another device, voice input, and the physical remote
were not tested. Recheck model, firmware, package roles, and dependencies for
each device. Other Android TV products can have different requirements.

## Connection and baseline

Set `TV_ADB` to the installed ADB executable and `TV_SERIAL` to the selected
device's actual debugging endpoint. `TV_USER` is the current Android user, not
an assumed account number. These examples use a POSIX shell; use equivalent
quoting on other hosts.

```sh
"$TV_ADB" devices -l
"$TV_ADB" -s "$TV_SERIAL" shell getprop ro.product.model
"$TV_ADB" -s "$TV_SERIAL" shell getprop ro.build.version.release
"$TV_ADB" -s "$TV_SERIAL" shell getprop ro.build.display.id
"$TV_ADB" -s "$TV_SERIAL" shell am get-current-user
"$TV_ADB" -s "$TV_SERIAL" shell pm list packages --user "$TV_USER"
"$TV_ADB" -s "$TV_SERIAL" shell pm list packages -d --user "$TV_USER"
"$TV_ADB" -s "$TV_SERIAL" shell pm list packages -3 --user "$TV_USER"
"$TV_ADB" -s "$TV_SERIAL" shell cmd package resolve-activity --brief --user "$TV_USER" \
  -a android.intent.action.MAIN -c android.intent.category.HOME
"$TV_ADB" -s "$TV_SERIAL" shell cmd package query-activities --brief --user "$TV_USER" \
  -a android.intent.action.MAIN -c android.intent.category.HOME
"$TV_ADB" -s "$TV_SERIAL" shell settings --user "$TV_USER" get secure enabled_accessibility_services
"$TV_ADB" -s "$TV_SERIAL" shell settings --user "$TV_USER" get secure always_on_vpn_app
"$TV_ADB" -s "$TV_SERIAL" shell settings --user "$TV_USER" get secure always_on_vpn_lockdown
"$TV_ADB" -s "$TV_SERIAL" shell cat /proc/sys/kernel/random/boot_id
```

Save `dumpsys package <package>` before changing each package. The affected
`User <id>` entry records its original `enabled` state and component overrides.
Keep the original Home component as part of the rollback.

## Candidate packages

These five packages were disabled for the recorded device. Evaluate their use
before applying the same choice elsewhere. The installed streaming apps were
kept enabled.

| Package | Role | Decision boundary |
| --- | --- | --- |
| `com.google.android.adservices.api` | Advertising APIs | Optional candidate; verify the installed package and current platform role. |
| `com.google.android.ondevicepersonalization.services` | On-device personalization | Optional candidate; check required personalization features. |
| `com.google.android.federatedcompute` | Federated computation for personalization | Optional candidate; check dependencies with personalization. |
| `com.google.android.feedback` | Feedback and diagnostic reporting | Optional candidate; preserve it when feedback collection is needed. |
| `com.google.android.play.games` | Google Play Games | Keep enabled when the household uses its games or features. |

Set `TV_PACKAGE` to one selected, installed package. Disable it, stop on failure,
and read back the affected user state. There is no bulk uninstall command in
this profile.

```sh
"$TV_ADB" -s "$TV_SERIAL" shell pm disable-user --user "$TV_USER" "$TV_PACKAGE"
"$TV_ADB" -s "$TV_SERIAL" shell dumpsys package "$TV_PACKAGE"
```

Keep Play services, the Play Store, networking, permission controls, system UI,
Settings, update services, casting receivers, voice input, remote services, and
accessibility packages. Examples on the tested model include
`com.google.android.apps.mediashell`, `com.google.android.katniss`,
`com.google.android.tv.remote.service`, and `com.google.android.tv.dfuservice`.
Do not infer that `com.google.android.tv.remotecontrol.logging` is expendable
from its name. It was left enabled. The old TV recommendations package was
already disabled and stayed that way.

## Launcher handoff

Official Projectivy package: `com.spocky.projengmenu`.
The verified Home component was
`com.spocky.projengmenu/.ui.home.MainActivity`; resolve and verify it on the
installed version before use.

Complete onboarding, decline optional anonymous reporting, and confirm the
Home activity runs. Notification, TV-listing, and accessibility access were
not needed for the recorded native Home setup.

The tested Streamer had two stock Home candidates:

| Package | Home component | Observed behavior |
| --- | --- | --- |
| `com.google.android.apps.tv.launcherx` | `.home.HomeActivity` | Priority 2; remained the resolved Home despite setting Projectivy as default. |
| `com.google.android.tungsten.setupwraith` | `.RecoveryActivity` | Priority 1; another Home candidate above Projectivy. |

Both packages were disabled only after Projectivy worked. Disabling an
individual privileged launcher component was rejected by Android. Package
disables were supported. Do not keep retrying a denied component change.

Check ownership of the active Wi-Fi configuration before disabling a setup
package. The recorded device used `android.uid.system:1000`, not the setup
package, as its Wi-Fi owner. Inspect only ownership fields from `dumpsys wifi`;
do not log the full network dump. Missing or ambiguous ownership is not proof
that disabling the package is safe. Keep the package enabled when dependencies
or network recovery are uncertain. Setup packages can also affect sound and
volume controls on other manufacturers' TVs.

For a confirmed matching profile with a working replacement and recovery path:

```sh
"$TV_ADB" -s "$TV_SERIAL" shell cmd package set-home-activity --user "$TV_USER" \
  com.spocky.projengmenu/.ui.home.MainActivity
"$TV_ADB" -s "$TV_SERIAL" shell pm disable-user --user "$TV_USER" com.google.android.apps.tv.launcherx
"$TV_ADB" -s "$TV_SERIAL" shell pm disable-user --user "$TV_USER" com.google.android.tungsten.setupwraith
"$TV_ADB" -s "$TV_SERIAL" shell input keyevent KEYCODE_HOME
```

Resolve Home again and inspect the foreground activity. `Success` from
`set-home-activity` alone did not prove the Home handoff on the tested device.

## Reduced motion

Read and save each value before changing it:

```sh
"$TV_ADB" -s "$TV_SERIAL" shell settings get global window_animation_scale
"$TV_ADB" -s "$TV_SERIAL" shell settings get global transition_animation_scale
"$TV_ADB" -s "$TV_SERIAL" shell settings get global animator_duration_scale
```

When requested, set the three values to `0.0`. In Projectivy's current UI,
find Appearance → Wallpaper → Image transition and choose None. Verify the
actual labels instead of depending on this path remaining unchanged.

```sh
"$TV_ADB" -s "$TV_SERIAL" shell settings put global window_animation_scale 0.0
"$TV_ADB" -s "$TV_SERIAL" shell settings put global transition_animation_scale 0.0
"$TV_ADB" -s "$TV_SERIAL" shell settings put global animator_duration_scale 0.0
```

## Verification and rollback

Check the actual foreground activity through `dumpsys activity activities`.
Resolve a streaming app's `MAIN` / `LEANBACK_LAUNCHER` activity before opening
it with `am start -W --user <id> -n <component>`. Check its result and return
with Home. Do not play a title or select an account just to prove app launch.

For each package changed, restore its recorded state for the same user:
`pm default-state` for original state 0, `pm enable` for original state 1,
or the matching original disabled state. Restore the stock Home packages and
the original Home component before removing the replacement launcher. Never
remove a pre-existing custom launcher as cleanup.

For each animation value, use `settings put global <key> <original-value>`.
When the original value was `null`, use `settings delete global <key>`.
Restore any launcher preference changed on a pre-existing installation too.

After a restart, verify a new boot ID and read back Home, package, and animation
states. The recorded Streamer retained those changes. Tailscale needed to be
opened once to reconnect. A known LAN endpoint allowed recovery; always-on VPN
settings were left unchanged. Do not promise automatic remote access after a
restart based only on a pre-restart tailnet ping.

## Sources

- [Google ADB reference](https://developer.android.com/tools/adb)
- [Official Android Platform Tools](https://developer.android.com/tools/releases/platform-tools)
- [Projectivy developer repository and releases](https://github.com/spocky/miproja1)
- [Projectivy website and purchase information](https://projectivylauncher.com/)
- [Community package descriptions](https://github.com/Universal-Debloater-Alliance/universal-android-debloater-next-generation/blob/main/resources/assets/uad_lists.json): A research lead, not proof of device-specific safety.
