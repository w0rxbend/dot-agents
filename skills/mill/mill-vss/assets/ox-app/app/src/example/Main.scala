package example

import ox.{Ox, OxApp}

object Main extends OxApp.Simple:
  def run(using Ox): Unit = println("VSS with Mill and Ox")
