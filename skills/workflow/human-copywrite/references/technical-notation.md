# Technical notation

Style and usage rules mostly or only for developer documentation.

For a specific programming language, follow its capitalization style.

## Code

Use code font for code.

Pick one punctuation-spacing method; use it consistently. "English-style" spacing (one space character between words) often works best: easy to remember and keep.

```
{height, width: extended; quo: integer); PageSize =
1024
```

## Syntax descriptions

- Code font for **literals** (parts of the language, values, and so on).
- **Italics** for placeholder names.
- **Regular text** for brackets enclosing something optional.
- Watch punctuation closely.

```
Read ([file,] var)
```

- Embedded caps to join words forming one placeholder name (`sourceFile`).
- Name placeholders consistently; for example, don't alternate between `commands` and `commandList`.

## Code font in text

Most developer documentation uses code font for computer-language elements in text. Other documents: judgment call.

- Code font for all text fragments that are programming-language expressions.
- Code font for names of files, volumes, directories, and libraries.

  > `StandardCRuntime.o` library
  > `MainProg.c` file

- **Don't use a function or method name as a verb.**

  > Correct: Run `ls` on both directories.
  > Incorrect: `ls` both directories.
  > Correct: Use `cd` to change to the root directory.
  > Incorrect: `cd` to the root directory.

- **Don't mix fonts within a single word.** Rewrite to avoid pluralizing a code-font word.

  > Correct: values of type `integer`
  > Incorrect: `integer`s

- Punctuation after code-font text: regular font, not code font, unless the mark belongs to the computer-language element.

  > `NAN(004)`, `nan(4)`, and `NaN` are examples of acceptable input.

## Placeholder names in text

In running text, italicize placeholder names (artificial terms meaningful only in your documentation, replaced by a value or symbol). Spell exactly as in syntax description. Don't use a placeholder as a regular English term.

> Correct: Replace *volumeName* with a name of up to 12 characters.
> Correct: The volume name can be up to 12 characters long.
> Incorrect: The *volumeName* can be up to 12 characters long.

Avoid `foo`, `bar`, and `baz` as hierarchical or ordered placeholder names in code examples. Use names suggesting item kind.

> `TObject.`*FirstMethod*
> `TObject.`*SecondMethod*
