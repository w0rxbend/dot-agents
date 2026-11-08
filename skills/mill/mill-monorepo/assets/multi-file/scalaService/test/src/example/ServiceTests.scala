package example

import utest.*

object ServiceTests extends TestSuite:
  def tests: Tests = Tests:
    test("cross-language-call"):
      assert(new ScalaService().message("Mill") == "Hello, Mill from Scala")
