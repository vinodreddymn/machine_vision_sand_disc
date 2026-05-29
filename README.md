# DiskVisionInspector

Desktop application for single-station classical machine-vision inspection of circular abrasive discs. The current phase uses manual image/video upload, OpenCV, PySide6, PLC boundaries, and PostgreSQL persistence; the workflow is intentionally kept small so a later two-stage inspection line can be added cleanly.

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
python main.py --gui
```

The desktop GUI is still the default, so `python main.py` continues to work.

Headless LAN-accessible mode:

```powershell
python main.py --web
```

The web dashboard and REST API are served from:

```text
http://localhost:8000
```

`python main.py --headless` is kept as an alias for the same web/backend runtime
so headless deployments do not import the PySide6 GUI.

## Tests

```powershell
pytest
```

## Architecture

- `automation/`: single-station workflow and PLC boundary
- `vision/`: deterministic inspection algorithms and overlay generation
- `services/`: GUI-independent inspection engine plus FastAPI backend
- `web/`: React/Vite LAN dashboard served by FastAPI after build
- `gui/`: PySide6 widgets that act as a client of the workflow services
- `camera/`: USB, video file, RTSP, and future industrial camera source boundaries
- `dataset/`: human-in-the-loop dataset collection, label stats, and export tools
- `config/`: tolerances and application settings
- `outputs/`: generated inspection artifacts and logs
- `storage/`: PostgreSQL schema, serial generation, persistence, and retrieval services
- `data/`: sample images and reference assets

## Current workflow

1. Start a new part.
2. Upload an inspection image or video.
3. Inspect the disc at the single station.
4. If the part fails, pulse the reject actuator.
5. If the part passes, release it to the good-product path.
6. Show live feed, captured overlay, measurements, defect list, PLC action, and final disposition.

## Future extension points

- Replace manual uploads with USB or GigE SDK adapters implementing `IndustrialCamera`.
- Feed the camera stream into a worker thread and trigger capture from conveyor sensors.
- Replace `SimulatedPLCController` with the actual PLC adapter for reject outputs, conveyor release, and line interlocks.
- Add a second station controller, panel, and table/view layer when the two-stage inspection system is ready.
- Persist labeled inspection crops for future anomaly-detection training.

## Data collection mode

`DISK_VISION_MODE` defaults to `DATA_COLLECTION`. After each inspection the
operator can confirm the system prediction or override it. The operator label is
treated as ground truth.

Saved dataset structure:

```text
dataset/
  good/station1/full/
  good/station1/roi/
  good/station1/overlay/
  defect/station1/full/
  defect/station1/roi/
  defect/station1/overlay/
  metadata/
```

Station 2 folders are also created for future expansion.

## Network API

Headless mode exposes:

- `GET /api/status`
- `GET /api/cameras`
- `GET /api/inspection/latest`
- `GET /api/station1`
- `GET /api/station2`
- `GET /api/metrics`
- `GET /api/dataset/stats`
- `GET /api/history`
- `GET /api/logs`
- `POST /api/label`
- `POST /api/operator-label`
- `POST /api/upload`
- `POST /api/start-part`
- `POST /api/start-inspection`
- `POST /api/stop-inspection`
- `POST /api/reset-part`
- `POST /api/reset`
- `POST /api/shutdown`
- `GET /stream/station1`
- `GET /stream/station2`
- `GET /image/station1/overlay`
- `GET /image/station2/overlay`
- `WebSocket /ws/logs`

## Web dashboard development

```powershell
cd web
npm install
npm run dev
```

For production serving through FastAPI:

```powershell
python main.py --web
```

`--web` starts the FastAPI backend and serves the React dashboard with one
command. If `web/dist` is missing, it automatically runs `npm install` if needed
and `npm run build` before starting the server.

## Dataset export

```powershell
python -c "from dataset.exporter import DatasetExporter; print(DatasetExporter().export_generic())"
```

This writes `dataset_export/images`, `dataset_export/labels`,
`dataset_export/metadata`, and `dataset_export/metadata.csv`.

## Docker

```powershell
docker compose up --build
```

The service exposes the dashboard on port `8000` and keeps `dataset/`,
`dataset_export/`, and `outputs/` mounted from the project directory.

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

Each completed inspection receives a serial such as:

```text
SINGLE-20260517-143522-000001
```

Stored data includes:

- physical part id
- station code
- inspection serial number
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
