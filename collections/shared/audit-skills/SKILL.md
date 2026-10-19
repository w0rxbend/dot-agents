---
name: audit-skills
description: "Statically audit a third-party agent skill or bundle before installing it - detect malicious commands, data exfiltration, privilege escalation, destructive or persistence behavior and obfuscated payloads across Windows, macOS, Linux and mobile, without executing it. Use when vetting an untrusted skill or bundle for safety."
category: security
risk: safe
source: community
date_added: "2026-03-07"
author: MAIOStudio
tags: [security, audit, skills, bundles, cross-platform]
---

# Audit Skills

Statically audit a third-party agent skill or bundle before installing it: read its files and flag malicious commands, data exfiltration, destructive or persistence behavior, and obfuscated payloads. Never execute the code under review.

## When to Use This Skill

- Use when you need to audit AI skills and bundles for security vulnerabilities
- Use when working with cross-platform security analysis
- Use when the user asks about verifying skill legitimacy or performing security reviews
- Use when scanning for mobile threats in AI skills

## How It Works

Read every file in the skill or bundle (SKILL.md, scripts, bundled binaries, manifests) without running any of it, and check for the patterns below across the platforms it targets.

### Platform-specific threats

#### 1. Privilege, Ownership & Metadata Manipulation
- **Elevated Access**: `sudo`, `chown`, `chmod`, `TakeOwnership`, `icacls`, `Set-ExecutionPolicy`.
- **Metadata Tampering**: `touch -t`, `setfile` (macOS), `attrib` (Windows), `Set-ItemProperty`, `chflags`.
- **Risk**: Unauthorized access, masking activity, or making files immutable.

#### 2. File/Folder Locking & Resource Denial
- **Patterns**: `chmod 000`, `chattr +i` (immutable), `attrib +r +s +h`, `Deny` ACEs in `icacls`.
- **Global Actions**: Locking or hiding folders in `%USERPROFILE%`, `/Users/`, or `/etc/`.
- **Risk**: Denial of service or data locking.

#### 3. Script Execution & Batch Invocation
- **Legacy/Batch Windows**: `.bat`, `.cmd`, `cmd.exe /c`, `vbs`, `cscript`, `wscript`.
- **Unix Shell**: `.sh`, `.bash`, `.zsh`, `chmod +x` followed by execution.
- **PowerShell**: `.ps1`, `powershell -ExecutionPolicy Bypass -File ...`.
- **Hidden Flags**: `-WindowStyle Hidden`, `-w hidden`, `-noprofile`.

#### 4. Dangerous Install/Uninstall & System Changes
- **Windows**: `msiexec /qn`, `choco uninstall`, `reg delete`.
- **Linux/Unix**: `apt-get purge`, `yum remove`, `rm -rf /usr/bin/...`.
- **macOS**: `brew uninstall`, deleting from `/Applications`.
- **Risk**: Removing security software or creating unmonitored installation paths.

#### 5. Mobile Application & OS Security (Android/iOS)
- **Android Tools**: `adb shell`, `pm install`, `am start`, `apktool`, `dex2jar`, `keytool`.
- **Android Files**: Manipulation of `AndroidManifest.xml` (permissions), `classes.dex`, or `strings.xml`.
- **iOS Tools**: `xcodebuild`, `codesign`, `security find-identity`, `fastlane`, `xcrun`.
- **iOS Files**: Manipulation of `Info.plist`, `Entitlements.plist`, or `Provisioning Profiles`.
- **Mobile Patterns**: Jailbreak/Root detection bypasses, hardcoded API keys in mobile source, or sensitive permission requests (Camera, GPS, Contacts) in non-mobile skills.
- **Risk**: Malicious mobile package injection, credential theft from mobile builds, or device manipulation via ADB.

#### 6. Information Disclosure & Network Exfiltration
- **Patterns**: `curl`, `wget`, `Invoke-WebRequest`, `Invoke-RestMethod`, `scp`, `ftp`, `nc`, `socat`.
- **Sensible Data**: `.env`, `.ssh`, `cookies.sqlite`, `Keychains` (macOS), `Credentials` (Windows), `keystore` (Android).
- **Intranet**: Scanning internal IPs or mapping local services.

#### 7. Service, Process & Stability Manipulation
- **Windows**: `Stop-Service`, `taskkill /f`, `sc.exe delete`.
- **Unix/Mac**: `kill -9`, `pkill`, `systemctl disable/stop`, `launchctl unload`.
- **Low-level**: Direct disk access (`dd`), firmware/BIOS calls, kernel module management.

#### 8. Obfuscation & Persistence
- **Encoding**: `Base64`, `Hex`, `XOR` loops, `atob()`.
- **Persistence**: `reg add` (Run keys), `schtasks`, `crontab`, `launchctl` (macOS), `systemd` units.
- **Remote script piping**: network fetch commands that stream directly into a shell or PowerShell evaluator.

#### 9. Legitimacy & Scope (Universal)
- **Registry Alignment**: If the skill came from a registry or catalog (in dot-agents, `catalog.json`), check that its recorded source, license and name match the files under review.
- **Structural Integrity**: Does it follow the standard repo layout?
- **Healthy Scope**: Does a "UI Design" skill need `adb shell` or `sudo`?

### Reporting

Write a security report with one verdict (safe to install, install with changes, or reject), the platforms targeted, each flagged action with its file and line and the threat it poses, and mitigation recommendations. Use the verdict as the only rating; do not add a separate numeric score.

## Rules

- Never execute the code under review, and never modify it.
- Decode obfuscation before judging: Base64, hex, XOR loops, `atob()`, `eval` of assembled strings.
- Judge by scope: a "UI design" skill requesting `adb shell`, `sudo`, network egress or filesystem writes outside its directory is a red flag.

## Done when

- Every file was read and any obfuscated payload decoded.
- The report gives the verdict, the platforms targeted, each flagged action with its file and line,.

## Related Skills

- `code-audit` - SAST of first-party source code.
- `dependency-scanning` - third-party CVEs and SBOMs.
