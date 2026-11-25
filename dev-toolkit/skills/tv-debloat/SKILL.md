---
name: tv-debloat
description: Debloat a Google TV or Android TV device through authorized ADB access. Set up a clean launcher, disable selected unwanted packages, reduce animations when requested, and verify restart recovery with a saved rollback. Use for an owned or authorized TV or streamer, not browser debugging, phone cleanup, rooting, or firmware changes.
---

# TV debloat

Make the requested TV easier to use with reversible changes. Preserve installed
streaming apps, sign-ins, casting, voice control, remote services, updates,
accessibility, and the connection used to manage it.

## Identify and connect

Use the device named by the user. Resolve its current address from the LAN or
tailnet, then confirm the model and Android version through ADB. Select that
device with `adb -s <serial>` for every device command. A tailnet name or an
open port does not establish ADB authorization.

Use installed Android Platform Tools, or obtain them from
[Google](https://developer.android.com/tools/releases/platform-tools). Try the
known debugging endpoint; do not scan unrelated devices. Modern wireless
debugging can use separate pairing and connection ports instead of port 5555.
Let the user enable debugging and approve the computer on the TV. If the TV
requires Wi-Fi for wireless debugging, recheck its address after the switch.

Reuse known setup receipts when the user asks to match an earlier TV. A standard
Streamer setup can proceed when the user makes that scope clear; finding an old
package list need not block it.

## Save the original state

Before the first change, create a private, device-specific receipt directory.
Keep the original snapshot unchanged if the task resumes. Save:

- Model, Android version, build, current user, and a device identity for reconnects.
- Installed, disabled, and third-party package lists for the affected user.
- Current Home handler and other Home candidates.
- Original enabled state for each package that will change.
- Original animation values, including whether a setting is absent.
- Existing accessibility services and VPN startup settings if relevant.
- Boot ID or boot count before the restart.

Do not copy account data, Wi-Fi credentials, pairing codes, or ADB private keys
into receipts. Keep private device details and screenshots out of public repos.
Write restore commands before disabling a launcher or system package.

For a Google TV Streamer or a Projectivy launcher handoff, read
[the device profile and command reference](references/google-tv-streamer.md).
Its package list records a tested setup, not a universal Android allowlist.

## Apply the requested changes

Prefer `pm disable-user --user <id>` to uninstalling packages. Keep package data
and existing disabled states. Match each candidate to the installed inventory
and the user's actual use. Leave unknown system packages enabled.

For a clean home screen, install Projectivy from its official Play listing or
[developer releases](https://github.com/spocky/miproja1/releases). Verify the
release digest when supplied. Finish onboarding and confirm the new Home
activity works before disabling the stock launcher. Check device-specific
dependencies before changing a recovery or setup package.

Use the current UI for onboarding and settings. With ADB UI automation, inspect
the hierarchy and the focused row, then use directional keys and read back the
result. A focused parent can contain an unfocused text label. Menu names change
between versions; inspect instead of guessing activity names or menu paths.
Decline optional reporting and avoid extra notification, TV-listing, or
accessibility access unless the requested function needs it. Preserve existing
accessibility features.

When reduced motion is requested, save and change the three system animation
scales. Also disable wallpaper transitions in the launcher if available.
Do not force background-process limits or disable update and security services
as a general performance shortcut.

Projectivy's free version supports this setup. Treat paid customization as a
separate user choice. Check current terms and price only when relevant, and
honor a decision to defer it.

## Verify and recover

Check the resolved Home handler and actual foreground activity. Open Settings
and representative installed streaming apps, then send Home and confirm the
replacement launcher returns. Read back package and animation states. Package
presence alone does not prove playback, casting, or voice input.

When a restart is within scope and local recovery is available, restart once
and compare the boot ID or count. A reboot command can time out because the TV
disconnected; inspect its state before considering another restart. Confirm
the launcher and settings persist after boot.

If tailnet access drops, use the known LAN endpoint when available and verify
the same device identity before further changes. In the recorded Streamer
setup, opening the existing Tailscale app restored its connection after boot.
Report whether reconnection was automatic or needed that action. Do not silently
change always-on VPN settings. If no recovery path is available, report the
restart check as pending instead of claiming a pass.

Leave the TV at its working home screen. Report the changes, verified behavior,
remaining checks, and restore location. Distinguish an app launch from playback
and an ADB Home command from a physical remote test.
