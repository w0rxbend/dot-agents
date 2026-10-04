# Native ownership and publication compatibility

## OpenCV ownership

Establish whether an API returns owned data, borrows an object, transfers a handle, or consumes a high-level image. In scalacv, `Managed.release` detaches once, `take` transfers without freeing, and `use`/`scope` clean up on exceptional paths. Register each acquisition immediately; allocating several Mats before entering a finally block leaks earlier objects if a later allocation fails. An adopted existing handle must not acquire a second independent owner. A value leaving a scope must be plain data or separately owned, never a scoped native object. See [ownership and scoped-acquisition implementation](https://github.com/worxbend/scalacv/blob/4bdd86f7ac8dfcc68f733f3105760a7251df1ba4/core/src/scalacv/Managed.scala).

Atomic release prevents a second free; it does not establish that concurrent native use and release are safe. Keep thread-safety claims separate. Tests should check consumption/reuse errors before JNI, exception cleanup, transfer versus copy, and release count. Native-memory regressions need the project's native leak/RSS harness; JVM heap assertions cannot see Mat buffers.

Route new native operations through the existing [OpenCv.load boundary](https://github.com/worxbend/scalacv/blob/4bdd86f7ac8dfcc68f733f3105760a7251df1ba4/core/src/scalacv/OpenCv.scala). Its bundled dependency resolution deliberately avoids eager loading of the whole JavaCPP OpenCV preset and speculative ELF/Mach-O loads: those can add headless GUI dependencies or interpose an incompatible system OpenCV ABI. Preserve its platform-specific loading rules and containment checks; an unparseable linker error does not justify bulk loading.

At interop boundaries, preserve channel order, depth, dimensions, stride, and ownership. A cropped or padded raster is not necessarily one continuous byte array. The reviewed conversion handles non-contiguous Mats separately, validates supported depths/channels, uses widened size arithmetic, and releases the allocation if filling it throws. See [Mat and BufferedImage conversion](https://github.com/worxbend/scalacv/blob/4bdd86f7ac8dfcc68f733f3105760a7251df1ba4/core/src/scalacv/Interop.scala).

## Build JVM, bytecode floor, and Scala floor

These are independent choices. The reviewed scalacv build bootstraps Mill with JDK25 while intentionally publishing Scala3.3.8 LTS and Java17 bytecode. TASTy compatibility is a compiler concern, and a newer build JVM must not silently raise either consumer floor. Its JDK matrix reads `MILL_JVM_ID` through a tracked task input; setting `JAVA_HOME` while every module pins another JDK does not test the claimed matrix. Read the current build instead of copying these snapshot versions. See [compatibility, toolchain, native classifier, and POM configuration](https://github.com/worxbend/scalacv/blob/4bdd86f7ac8dfcc68f733f3105760a7251df1ba4/build.mill).

Separate portable APIs from platform-specific native binaries. scalacv publishes classifier-less OpenCV API dependencies; host classifiers belong to test/example/runtime setup. Validate both Linux and other supported classifiers and reject combinations for which upstream publishes no native artifact. Inspect generated POMs rather than assuming Mill strips classifiers as intended. Preserve published artifact names and optional effect integration modules.

## Contract checks

For scalacv, the reviewed CI separates selectors with `+` where test commands otherwise consume following arguments: `./mill core.test + zio.test + examples.test`. It also runs `docs.mdocCheck`, `leaks.test`, POM assertions, and a Java consumer smoke. Choose the subset relevant to the change and follow the current [consumer/JDK/publication checks](https://github.com/worxbend/scalacv/blob/4bdd86f7ac8dfcc68f733f3105760a7251df1ba4/.github/workflows/ci.yml).

For Gitea, preserve its Java21 API floor, warnings that catch discarded ZIO effects, and the checked-in `compatibility.check` baseline. For Codeberg4s, use its current formatter, Scalafix, coverage, and MiMa configuration rather than swapping to another library's gates. These are maintained contracts, not universal Scala flags. See [Gitea modules and public API gate](https://github.com/worxbend/gitea-scala-client/blob/2590501c22c8dd0bba216c24b2e03e6da873b313/build.mill) and [Codeberg modules and compatibility configuration](https://github.com/worxbend/codeberg4s/blob/94fe214cccd7b077b9151ab456e256931cb69800/build.mill).
