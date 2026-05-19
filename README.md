# DiskVisionInspector

Starter desktop application for two-stage classical machine-vision inspection of circular abrasive disks. The current phase uses manual image upload, OpenCV, and PySide6; camera, trigger, PLC, conveyor, flipper, and AI hooks are isolated so they can be added without rewriting the inspection core.

## VS Code setup

```powershell
cd DiskVisionInspector
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
code .
```

If Python 3.11 is not installed, any Python `3.11+` interpreter is acceptable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Tests

```powershell
pytest
```

## Architecture

- `automation/`: two-station workflow and PLC boundary
- `vision/`: deterministic inspection algorithms and overlay generation
- `gui/`: PySide6 widgets only; no inspection logic hidden in the UI
- `camera/`: camera interface and simulator for future live acquisition
- `config/`: tolerances and application settings
- `outputs/`: generated inspection artifacts and logs
- `storage/`: PostgreSQL schema, serial generation, persistence, and retrieval services
- `data/`: sample images and reference assets

## Current workflow

1. Start a new part.
2. Upload the Station 1 top-side image and run inspection.
3. If Station 1 fails, request the Station 1 reject actuator and skip Station 2.
4. If Station 1 passes, release the part toward the mechanical flipper.
5. Upload the Station 2 flipped-side image and run inspection.
6. If Station 2 fails, request the Station 2 reject actuator; otherwise release the part to the good-product path.
7. Show both live-feed panes, captured overlays, per-station measurements, PLC action, and final disposition.

## Future extension points

- Replace manual uploads with USB or GigE SDK adapters implementing `IndustrialCamera`.
- Feed both camera streams into worker threads and trigger capture from conveyor sensors.
- Replace `SimulatedPLCController` with the actual PLC adapter for reject outputs, conveyor release, and line interlocks.
- Add part tracking between stations so the same product identity follows the flip stage.
- Persist labeled inspection crops for future anomaly-detection training.

## PostgreSQL persistence

Inspection records are stored in PostgreSQL using credentials from `storage/.env`.

Example:

```powershell
POSTGRES_DB=diskvision
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

You can still override the file at launch time with a full DSN:

```powershell
$env:DISK_VISION_POSTGRES_DSN = "dbname=diskvision user=postgres password=YOUR_PASSWORD host=localhost port=5432"
python main.py
```

Each completed stage receives a serial such as:

```text
S1-20260517-143522-000001
S2-20260517-143541-000001
```

Stored data includes:

- physical part id
- stage
- stage serial number
- inspection timestamp
- decision
- final disposition
- source image name
- reject request flag
- all measurements
- defect list
- saved overlay path

Retrieval helpers are available from `InspectionStorageService`:

- `recent(limit)`
- `for_part(physical_part_id)`
- `for_stage(stage, limit)`


cd C:\Users\DELL\Documents\AI_Projects\DiskVisionInspector

(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\DELL\Documents\AI_Projects\DiskVisionInspector\.venv\Scripts\Activate.ps1)

python main.py 
