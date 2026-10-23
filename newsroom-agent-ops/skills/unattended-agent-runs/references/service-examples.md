# Supervised service examples

These examples show the required relationships. Replace placeholders with
reviewed local paths and commands. Keep credentials outside unit files and task
arguments.

## Linux: systemd user services

Use one unit for the persistent session and one for the producer. Pin both
working and state directories.

    [Unit]
    Description=Newsroom agent session
    After=network-online.target

    [Service]
    Type=simple
    WorkingDirectory=<working-dir>
    Environment=AGENT_STATE_DIR=<state-dir>
    ExecStart=<session-launcher>
    Restart=on-failure
    RestartSec=10
    MemoryHigh=1500M
    MemoryMax=2G
    MemorySwapMax=512M
    CPUQuota=300%

    [Install]
    WantedBy=default.target

    [Unit]
    Description=Newsroom work producer
    After=newsroom-agent-session.service

    [Service]
    Type=simple
    WorkingDirectory=<working-dir>
    Environment=AGENT_STATE_DIR=<state-dir>
    ExecStart=<producer-command>
    Restart=on-failure
    RestartSec=10

    [Install]
    WantedBy=default.target

Enable the user service and configure user-service persistence according to the
operating system's documented linger policy. Then perform a real reboot and
verify the producer, session, state directory, and resource limits.

## macOS: launchd

Use a LaunchAgent for user-scoped work. Keep WorkingDirectory and the state
environment variable explicit.

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
      "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
      <key>Label</key>
      <string>org.example.newsroom-agent</string>
      <key>ProgramArguments</key>
      <array>
        <string>&lt;session-launcher&gt;</string>
      </array>
      <key>WorkingDirectory</key>
      <string>&lt;working-dir&gt;</string>
      <key>EnvironmentVariables</key>
      <dict>
        <key>AGENT_STATE_DIR</key>
        <string>&lt;state-dir&gt;</string>
      </dict>
      <key>KeepAlive</key>
      <true/>
      <key>ThrottleInterval</key>
      <integer>10</integer>
      <key>StandardOutPath</key>
      <string>&lt;log-dir&gt;/session.out.log</string>
      <key>StandardErrorPath</key>
      <string>&lt;log-dir&gt;/session.err.log</string>
    </dict>
    </plist>

launchd does not provide the same cgroup controls as systemd. Apply platform
resource controls in the launcher, and prove that restart and login behavior
match the operating plan.

## Windows: Task Scheduler

Use two explicit tasks or one supervised launcher. Set the working directory in
the action. Do not rely on the scheduler's default directory.

    $action = New-ScheduledTaskAction -Execute "<session-launcher.exe>" -Argument "--state-dir <state-dir>" -WorkingDirectory "<working-dir>"
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName "Newsroom agent session" -Action $action -Trigger $trigger -Settings $settings

Task Scheduler can reject or terminate long tasks according to task settings.
Review execution limits, battery rules, login requirements, and restart
behavior. The lease remains the source of single-flight truth.

## Reboot proof

After a real reboot, verify:

1. The supervisor is active.
2. The producer is active.
3. Both use the pinned working and state directories.
4. The agent reads the expected inbox.
5. A synthetic local run completes through the explicit done step.
6. The summary is delivered once.
7. Resource limits or launcher controls are active.
8. No second instance owns the same lease.
