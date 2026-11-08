package example

final class ScalaService:
  private val greeting: Greeting = new KotlinGreeting()
  def message(name: String): String = greeting.greet(name) + " from Scala"
