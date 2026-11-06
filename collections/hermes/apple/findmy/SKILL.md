---
name: findmy
description: "Track Apple devices/AirTags via FindMy.app on macOS."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [FindMy, AirTag, location, tracking, macOS, Apple]
---

# Find My (Apple)

## Prerequisites

- **macOS** with Find My app and iCloud signed in
- Devices/AirTags already registered in Find My
- Screen Recording permission for terminal (System Settings → Privacy → Screen Recording)
- **Optional but recommended**: install `peekaboo` for better UI automation:
  `brew install steipete/tap/peekaboo`

## When to Use

- User asks "where is my [device/cat/keys/bag]?"
- Tracking AirTag locations
- Checking device locations (iPhone, iPad, Mac, AirPods)
- Monitoring pet or item movement over time (AirTag patrol routes)

## Method 1: AppleScript + Screenshot (Basic)

### Open FindMy and Navigate

```bash
# Open Find My app
osascript -e 'tell application "FindMy" to activate'

# Wait for it to load
sleep 3

# Take a non-interactive screenshot (Find My is frontmost after activate).
# Do not use `screencapture -w`: it waits for a mouse click and blocks the agent.
# Captures whole screen: hide other sensitive windows first, or use Method 2 (app-only).
screencapture -x ~/.hermes/cache/scratch/findmy.png
```

Read screenshot with `vision_analyze`:
```
vision_analyze(image_url="~/.hermes/cache/scratch/findmy.png", question="What devices/items are shown and what are their locations?")
```

### Switch Between Tabs

```bash
# Switch to Devices tab
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Devices" of toolbar 1 of window 1
    end tell
end tell'

# Switch to Items tab (AirTags)
osascript -e '
tell application "System Events"
    tell process "FindMy"
        click button "Items" of toolbar 1 of window 1
    end tell
end tell'
```

## Method 2: Peekaboo UI Automation (Recommended)

If `peekaboo` installed, use it for more reliable UI interaction:

```bash
# Open Find My
osascript -e 'tell application "FindMy" to activate'
sleep 3

# Capture and annotate the UI
peekaboo see --app "FindMy" --annotate --path ~/.hermes/cache/scratch/findmy-ui.png

# Click on a specific device/item by element ID
peekaboo click --on B3 --app "FindMy"

# Capture the detail view
peekaboo image --app "FindMy" --path ~/.hermes/cache/scratch/findmy-detail.png
```

Analyze with vision:
```
vision_analyze(image_url="~/.hermes/cache/scratch/findmy-detail.png", question="What is the location shown for this device/item? Include address and coordinates if visible.")
```

## Workflow: Track AirTag Location Over Time

To monitor an AirTag (e.g., cat's patrol route):

```bash
# 1. Open FindMy to Items tab
osascript -e 'tell application "FindMy" to activate'
sleep 3

# 2. Click on the AirTag item (stay on page — AirTag only updates when page is open)

# 3. Periodically capture location — bounded: 12 captures x 5 min = 1 hour.
#    Agree the duration with the user; run it with background=true.
for i in $(seq 1 12); do
    osascript -e 'tell application "FindMy" to activate'
    peekaboo image --app "FindMy" --path ~/.hermes/cache/scratch/findmy-$(date +%H%M%S).png \
      || screencapture -x ~/.hermes/cache/scratch/findmy-$(date +%H%M%S).png
    sleep 300
done
```

Analyze each screenshot with vision to extract coordinates. Compile route from them.

## Limitations

- FindMy has **no CLI or API**. Must use UI automation.
- Location accuracy depends on nearby Apple devices in FindMy network
- AppleScript UI automation may break across macOS versions

## Rules

1. Keep FindMy app in foreground when tracking AirTags (updates stop when minimized)
2. Read screenshot content with `vision_analyze`. Do not try to parse pixels.
3. For ongoing tracking, cronjob may capture and log locations periodically: agree interval and end date with user; remove job when done.
4. Respect privacy: track only devices/items user owns
5. Screenshots hold location data: delete them after analysis (`rm -f ~/.hermes/cache/scratch/findmy*.png`).
