package example

class KotlinGreeting : Greeting {
    override fun greet(name: String): String = "Hello, $name"
}
