# Issue #001: Continuous alert marking for timelapse

## Context
Currently, only frames that trigger Telegram notifications are marked as alerts in the timelapse. This means if a person walks through the frame and lingers, only the first detection triggers an alert. The user wants ALL frames with detections to be visually marked in the timelapse viewer.

## Requirements
- Track active detection classes (person, animals) in memory
- Any frame with active classes → mark as alert
- When all classes disappear → clear tracking
- Simpler approach: mark all frames that pass through the detection loop

## Acceptance Criteria
- [ ] Frames with detections are marked as "alert" regardless of cooldown
- [ ] Alert markers persist for duration of detection
- [ ] No Telegram spam (only first detection in cooldown period sends notification)
- [ ] Visual indicator in timelapse viewer shows alert frames

## Files to Modify
- `server/stream_server.py` - detection loop tracking
- `server/timelapse.py` - alert marking on frames
