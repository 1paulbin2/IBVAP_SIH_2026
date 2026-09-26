# Analytics Rules

This directory contains the event and behaviour analytics logic for IBVAP.

## Rules implemented

### 1. Virtual-fence / zone detection

The geometry module checks whether a tracked object's point is inside a configured polygonal zone.

The rule supports:
- Objects inside the zone
- Objects outside the zone
- Points on the zone boundary

The polygon is provided as configuration/input, so the logic is not tied to one specific border location.

### 2. Night-time movement

The night rule checks whether a timestamp falls within the configured night period.

The night period is configurable through:

`rules/rules_config.json`

Current test configuration:

- Night start: `18:00`
- Night end: `06:00`

The rule also supports periods that cross midnight.

### 3. Prolonged presence

An object is considered to have prolonged presence when its dwell time reaches or exceeds the configured threshold.

Current test configuration:

- Dwell threshold: `60` seconds

### 4. Suspicious-activity rule

The suspicious-activity rule uses explicit conditions rather than attempting to infer human intent.

An event is generated when all of these conditions are true:

1. Object is inside the restricted zone.
2. It is night-time.
3. The configured dwell threshold has been reached.

This makes the rule explainable and testable.

### 5. Event severity

Severity is calculated using explicit conditions:

- `LOW` — object is outside the restricted zone.
- `MEDIUM` — object is inside the zone.
- `HIGH` — object is inside the zone during night-time.
- `CRITICAL` — object is inside the zone during night-time and has prolonged presence.

### 6. Event correlation

Events can be checked for duplication using:

- Camera ID
- Track ID
- Event type
- Configured time window

This helps reduce repeated events for the same tracked object.

## False-alert considerations and limitations

These rules are intentionally conservative and condition-based. They do not determine a person's intent.

Possible false-alert situations include:

- A person legitimately entering a configured restricted area.
- A person remaining in an area for a legitimate reason.
- Tracking errors causing an object to appear to remain in a zone.
- Detection or tracking errors near a zone boundary.
- Incorrect camera time configuration affecting night-time classification.
- Temporary detection or tracking interruptions.

The rules should therefore be treated as event-generation logic for further review, not as proof of suspicious intent.

Thresholds and zones should be configured and validated for the deployment environment.

## Testing

The analytics modules are covered by automated pytest tests.

The test suite covers:

- Zone inside/outside behaviour
- Zone boundary input
- Night-time conditions
- Dwell-time thresholds
- Suspicious-activity conditions
- Event severity
- Event creation
- Event correlation
- End-to-end analytics integration

Run all tests with:

```powershell
py -m pytest -v
