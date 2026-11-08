---
name: parametric-cad-validation
description: Change and validate Python/build123d parametric models, manufacturing interfaces, CAD exports, and native FreeCAD save/reopen pipelines in the FreeCAD-Projects family. Use when editing geometry, presets or export code in a FreeCAD-Projects subproject, or when asked to prove a CAD change still fits and exports cleanly.
license: MIT
---

# Parametric CAD validation

Find target subproject before changing geometry. Each subproject (for example Tigerbee, Tigerbee 7inch, Tigerbeetle V2 and ChitinFPV; list repository root for current set) has own models, commands and artifact conventions. Similar component names do not mean identical parameters or interfaces. Read subproject's pyproject, lockfile, preset definitions, validation report and CI. Keep Python model as source of truth where FCStd is interchange artifact.

Read [geometry-gates.md](references/geometry-gates.md) for dimensional, topology and assembly changes. Read [native-export.md](references/native-export.md) for STEP/STL/FCStd output, separate FreeCAD runtimes and save/reopen evidence. Load both when geometry edit changes exported parts.

Validate changed part and shared interfaces, then relevant presets and assembly gates. Keep units and tolerances explicit. Report separately: measured geometry, missing equipment dimensions, native integration coverage. Generated file or nice viewport does not prove valid solid, geometric fit, or reopened native document.
