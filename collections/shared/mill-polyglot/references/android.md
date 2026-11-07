# Experimental Android workflows

Mill's Android docs call several example workflows rough/experimental. Assess SDK/tool/plugin/IDE support before using it for production Android app. Successful Mill build of Kotlin/JVM backend is no evidence of Android parity with existing Gradle project.

## SDK and source modules

Use `AndroidSdkModule` for SDK/build tools, plus app/library module (Java, Kotlin or Scala, as pinned release supports). App configuration covers compile/minimum SDK, application ID, namespace, SDK module reference, manifest/resources, build type. Keep identifiers and minSdk policy explicit; example values are illustrative.

Pin SDK command-line/build tools and compiler/plugin versions. Installation and license acceptance are external setup. Don't copy `autoAcceptLicenses = true` into user's build by default. Match Android SDK/license setup to task's actual authorization and environment. Emulators/AVDs have own availability, architecture, ports, lifecycle. List all required tooling; managed JDK is not whole setup.

## IDEs and tests

BSP import and generated IntelliJ/Android Studio project files differ in capability. Compose preview, resource/R-class navigation, file associations, Logcat support depend on version/IDE. Check documented limitations; don't claim full Gradle plugin integration.

Distinguish local JVM, Robolectric, and instrumented device/emulator tests. Instrumented tests need SDK/device, packaging/install, runner, startup/readiness, cleanup. Parallel suites need separate emulator ports/devices. Use quick local tests where they can validate behavior. Run representative instrumentation for Android-specific lifecycle/resources.

## Ecosystem examples

Compose sample shows Kotlin/Compose compiler settings, build-type sources, optimization. Hilt shows KSP/generated injection configuration. Koin examples include JVM/Robolectric behavior. Scala Android packages JVM bytecode for ART; needs supported Scala/runtime/API versions. Native examples use NDK/CMake and linking requirements, not Scala Native backend; keep those toolchains distinct.

Adopt only integrations project uses. Hilt/KSP version must match its Kotlin/compiler technology. Compose project may need embeddable compiler configuration. Wire generated source/resource paths as explicit task dependencies; do not copy them from old Gradle output directories.

## Packaging, signing, and libraries

Debug/release behavior, R8/ProGuard rules, signing metadata, APK/AAB outputs, native libraries need tested release configuration. Never reuse example keystore passwords. Keep signing secrets in environment inputs, out of cached/logged artifact metadata. Producing signed release and uploading/distributing it are separate operations, each with own user scope.

Publish Android libraries with AAR metadata via supported `AndroidLibModule`/publishing integration, not as ordinary JVM jar. Verify separate Android consumer resolves resources/manifest/dependencies. Android Native, JVM Scala Native, and GraalVM native-image are unrelated packaging paths despite sharing word native.

Sources: [initial setup](https://mill-build.org/mill/android/android-initial-setup.html), [Java](https://mill-build.org/mill/android/java.html), [Kotlin](https://mill-build.org/mill/android/kotlin.html), [Scala](https://mill-build.org/mill/android/scala.html), [IDE](https://mill-build.org/mill/android/ide.html), [linting](https://mill-build.org/mill/android/android-linting.html), [releases](https://mill-build.org/mill/android/android-release.html), [publishing](https://mill-build.org/mill/android/publishing.html), [Compose](https://mill-build.org/mill/android/compose-samples.html), [Hilt](https://mill-build.org/mill/android/hilt-sample.html), [Koin](https://mill-build.org/mill/android/koin_androidx_examples.html), [Native](https://mill-build.org/mill/android/android-native-example.html).
