# Experimental Android workflows

Mill's Android pages explicitly describe rough/experimental workflows in several examples. Assess SDK/tool/plugin/IDE support before choosing it for a production Android application. A Kotlin/JVM backend's successful Mill build is not evidence of Android parity with an existing Gradle project.

## SDK and source modules

Use an `AndroidSdkModule` for SDK/build tools and an appropriate application/library module: Java, Kotlin, or Scala integration as supported by the pinned release. App configuration includes compile/minimum SDK, application ID, namespace, SDK module reference, manifest/resources, and build type. Keep identifiers and minSdk policy explicit; examples' values are illustrative.

Pin SDK command-line/build tools and compiler/plugin versions. Installation/license acceptance is an external setup operation; don't copy `autoAcceptLicenses = true` into a user's build by default. Use the required Android SDK/license setup for the task's actual authorization and environment. Emulators/AVDs have separate availability, architecture, ports, and lifecycle; list required tooling rather than treating managed JDK as the whole setup.

## IDEs and tests

BSP import and generated IntelliJ/Android Studio project files have different capabilities. Compose preview, resource/R-class navigation, file associations, and Logcat support are version/IDE-dependent; verify the documented limitations instead of claiming full Gradle plugin integration.

Distinguish local JVM tests, Robolectric tests, and instrumented device/emulator tests. The latter need an SDK/device, packaging/install step, runner, startup/readiness, and cleanup. Parallel suites need separate emulator ports/devices. Keep local tests quick where they can validate behavior, and run representative instrumentation for Android-specific lifecycle/resources.

## Ecosystem examples

The Compose sample demonstrates Kotlin/Compose compiler settings, build-type sources, and optimization; Hilt demonstrates KSP/generated injection configuration. Koin examples include JVM/Robolectric behavior. Scala Android uses JVM bytecode packaged for ART and needs supported Scala/runtime/API versions. Native examples use NDK/CMake and linking requirements rather than the Scala Native backend; distinguish those toolchains.

Adopt only the integrations the project actually uses. A Hilt/KSP version must match its Kotlin/compiler technology, and a Compose project may require embeddable compiler configuration. Generated source/resource paths should be explicit task dependencies, not copied from previous Gradle output directories.

## Packaging, signing, and libraries

Debug/release behavior, R8/ProGuard rules, signing metadata, APK/AAB outputs, and native libraries need a tested release configuration. Never reuse example keystore passwords. Keep signing secrets in environment inputs and exclude them from cached/logged artifact metadata. Producing a signed release and uploading/distributing it are separate operations with their own user scope.

Android library publication uses AAR metadata and the supported `AndroidLibModule`/publishing integration, rather than treating the library as an ordinary JVM jar. Verify a separate Android consumer resolves resources/manifest/dependencies correctly. Android Native, JVM Scala Native, and GraalVM native-image are unrelated packaging paths despite sharing the word native.

Sources: [initial setup](https://mill-build.org/mill/android/android-initial-setup.html), [Java](https://mill-build.org/mill/android/java.html), [Kotlin](https://mill-build.org/mill/android/kotlin.html), [Scala](https://mill-build.org/mill/android/scala.html), [IDE](https://mill-build.org/mill/android/ide.html), [linting](https://mill-build.org/mill/android/android-linting.html), [releases](https://mill-build.org/mill/android/android-release.html), [publishing](https://mill-build.org/mill/android/publishing.html), [Compose](https://mill-build.org/mill/android/compose-samples.html), [Hilt](https://mill-build.org/mill/android/hilt-sample.html), [Koin](https://mill-build.org/mill/android/koin_androidx_examples.html), [Native](https://mill-build.org/mill/android/android-native-example.html).
