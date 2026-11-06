# Toolchain and bytecode compatibility

Mill's launcher JVM runs build definitions; `mill-jvm-version` selects it. Distribution/version strings can select managed JDKs. JVM modules each use `jvmVersion`. Compiler flags control emitted bytecode/API constraints. Three choices are related, not interchangeable. Defaults vary by Mill version: inspect effective values, do not assume whichever `java` is on PATH is used.

Runnable mixed example: application modules use `temurin:21.0.8`; Java `--release 21`, Scala `-release 21`, Kotlin `-jvm-target 21`. Compilers: Scala 3.8.2, Kotlin 2.2.20. Build launcher uses `system`, explicitly requiring installed compatible JDK; new CI project can swap in managed pin. Compiling on newer JDK for older target: verify Kotlin API constraints separately.

VSS: current official stack guidance uses Java 25 virtual threads and Scala 3. Give that service deliberate Java 25 toolchain and target per its deployment policy. Do not raise shared Java 17/21 API library's runtime minimum unless required. Service can consume older bytecode; reverse is not possible. Ox/Tapir and other libraries may impose minimum compiler/JDK versions independent of Mill.

Use JVM index/distribution options documented for project's Mill version; pin index/download for full repeatability. `system` is valid explicit local choice but depends on machine configuration. Unsupported OS/CPU distributions need tested alternate, not unreviewed URL. `./mill java`, `javac`, `javap`, `jps`, `jstack` expose build JVM tools on versions supporting these commands. Confirm they target intended JVM before troubleshooting application process.

Model runtime compatibility matrix with cross modules when it gives evidence a released library actually needs. Limit combinations to supported axes; do not multiply all Scala versions, JDKs, platforms and flags into expensive Cartesian product. JVM cross-building is not automatically Scala binary cross-build. Define each axis and its artifact/version policy deliberately.

Compiler plugins often impose tighter constraints than ordinary libraries: Scala full-version plugins, Kotlin compiler plugins tied to `kotlinVersion`, matching KSP/Kapt releases, annotation processors affected by JDK behavior. Generic JavaModule trait can centralize release flags; language traits need separate compiler settings. Verify settings on nested test modules so tests do not silently compile against newer runtime.

Spark: pick Scala/JDK matching actual Spark distribution. Scala.js/Native: align platform-specific compiler/runtime artifacts; JVM jar cannot satisfy Native or JS classpath. GraalVM native-image: pin distribution, test dynamic/reflection/resource behavior. Keep platform requirements with relevant module family, not in indiscriminate repository-wide convention.

Sources: [JVM versions](https://mill-build.org/mill/fundamentals/configuring-jvm-versions.html), [headers](https://mill-build.org/mill/cli/build-header.html), [cross builds](https://mill-build.org/mill/fundamentals/cross-builds.html), [Spark](https://mill-build.org/mill/scalalib/spark.html), [Scala configuration](https://mill-build.org/mill/scalalib/module-config.html), [Kotlin configuration](https://mill-build.org/mill/kotlinlib/module-config.html).
