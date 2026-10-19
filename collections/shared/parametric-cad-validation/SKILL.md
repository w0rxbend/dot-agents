---
name: parametric-cad-validation
description: Change and validate Python/build123d parametric models, manufacturing interfaces, CAD exports, and native FreeCAD save/reopen pipelines in the FreeCAD-Projects family. Use when editing geometry, presets or export code in a FreeCAD-Projects subproject, or when asked to prove a CAD change still fits and exports cleanly.
license: MIT
---

# Parametric CAD validation

Find the actual subproject before changing geometry. The portfolio contains separate subprojects (for example Tigerbee, Tigerbee 7inch, Tigerbeetle V2 and ChitinFPV; list the repository root for the current set), each with its own models, commands and artifact conventions; similar component names do not establish identical parameters or interfaces. Read its pyproject, lockfile, preset definitions, validation report and CI. Preserve the Python model as the source of truth where FCStd is an interchange artifact.

Read [geometry-gates.md](references/geometry-gates.md) for dimensional, topology and assembly changes. Read [native-export.md](references/native-export.md) for STEP/STL/FCStd output, separate FreeCAD runtimes and save/reopen evidence. Load both when a geometry edit changes exported parts.

Validate the changed part and shared interfaces, then the relevant presets and assembly gates. Keep units and tolerances explicit. Report measured geometry, missing equipment dimensions and native integration coverage separately. A generated file or attractive viewport does not establish a valid solid, geometric fit, or a reopened native document.
