package example;

public final class Main {
  public static void main(String[] args) {
    System.out.println(new ScalaService().message(args.length == 0 ? "Mill" : args[0]));
  }
}
