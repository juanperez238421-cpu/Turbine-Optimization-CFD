# Q1 real-CFD visualization pipeline

This directory implements a reproducible path from **real ANSYS CFX results** to publication-grade figures without using generative image synthesis.

## Why this architecture

ANSYS CFX `.res/.trn` files are proprietary. The defensible route is therefore two-stage:

1. **Licensed ANSYS workstation** — export the real CFX result to an open scientific format (EnSight Gold is the preferred route here; CGNS is also possible).
2. **Open post-processing** — render the exported data with VTK/PyVista using one fixed camera, plane, scalar range and visualization recipe across all compared cases.

The renderer supports EnSight/CGNS/VTK-family inputs through VTK/PyVista and produces:

- real mesh surface with edges;
- velocity-magnitude slice + streamlines;
- water-volume-fraction `0.5` free-surface iso-surface;
- pressure slice;
- vorticity slice when the exported field is present;
- `render_audit.json` recording file, field names, point/cell counts, domain bounds and global comparison ranges.

## Carolina-specific scientific safeguards

The project archive currently supports:

- **Parque I**: matched baseline case;
- **Logarithmic AI60**: ambiguous case identity, with CFX-16 and CFX-28 remaining candidate branches;
- **Hyperbolic AI90**: no unique recovered CFD case package.

For this reason the example manifest keeps ambiguous candidates explicitly labeled as candidates. The renderer does not rename a candidate as a verified design.

## Export real CFX data

On a Windows machine with ANSYS CFX installed:

```powershell
cd q1_cfd_visualization

./export_cfx_to_ensight.ps1 `
  -ResultsFile "D:\path\to\CFX_009.res" `
  -OutputBase "D:\exports\parque_i\parque_i"
```

If a specific transient timestep must be exported, provide `-Timestep N`.

The helper calls `cfx5export -ensight -geometry ...`. Keep the original `.res/.trn/.out` and export log together with the exported case for provenance.

## Prepare the real-data manifest

Copy:

```text
cases.carolina.example.json -> cases.carolina.json
```

Then change the `file` paths to the exported EnSight `.case`/`.encas`, CGNS `.cgns`, or VTK files.

For a Q1 comparison, define the **same**:

- slice plane origin and normal;
- final timestep;
- camera position;
- seed geometry for streamlines;
- VOF iso-value;
- scalar range across all cases.

The Python renderer calculates scalar ranges globally across the loaded cases so the final comparison does not use misleading per-panel autoscaling.

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python render_q1.py cases.carolina.json --output q1_rendered
```

On Linux/headless environments:

```bash
xvfb-run -a python render_q1.py cases.carolina.json --output q1_rendered
```

## GitHub Actions

`.github/workflows/q1-cfd-render.yml` validates the rendering environment using pinned PyVista/VTK versions. If a real `cases.carolina.json` and its data are available in the runner workspace, it also renders and uploads the figure set as a workflow artifact.

Large CFD data should **not** be committed blindly to GitHub. A 2–5 million-cell transient case can exceed normal repository limits. Use one of these approaches:

1. export only the final timestep and required variables for the paper;
2. store the exported scientific dataset in an institutional repository / Zenodo / controlled Drive and stage it into the runner;
3. use a self-hosted GitHub runner on the workstation where the exported data already exist.

A self-hosted runner is the cleanest route if repeated figures must be regenerated from large real cases.

## Minimum publication figure set for Carolina

### FIG-M10 — velocity + streamlines
- Parque I baseline;
- Log AI60 only after CFX-16 vs CFX-28 is resolved, or show both candidates explicitly during forensic comparison;
- identical plane, seeds, camera and global velocity range.

### FIG-M11 — free surface / air core
- water volume fraction iso-surface at the same threshold (normally 0.5);
- identical camera and clipping;
- same final time/window.

### FIG-M12 — mechanistic field
- pressure and/or vorticity;
- use the same scalar limits across cases;
- do not infer a mechanism from an unmatched case.

## What this pipeline does not prove

A polished image does not establish:

- mesh independence;
- time-step independence;
- GCI;
- experimental validation;
- correct design identity.

Those remain separate verification/validation tasks.

## Reproducibility record

Every production run should archive:

- source `.res/.trn/.out` SHA-256;
- export command and ANSYS release;
- exported data SHA-256;
- `cases.carolina.json`;
- `render_audit.json`;
- renderer commit SHA;
- final PNG/TIFF/PDF checksum.

This makes every manuscript field figure traceable from source CFD result to publication asset.
