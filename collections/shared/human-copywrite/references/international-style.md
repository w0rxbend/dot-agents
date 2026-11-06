# International style

International style helps readers with limited English proficiency. It also helps translators, human or machine, localize writing by reducing cultural and customary language burdens.

Basic rules:
- Write in simple structures.
- Don't use idiomatic or colloquial expressions.
- Avoid shortcuts, symbols, and abbreviations that could easily be spelled out.
- Express data with the international standards below. Deviate only when a proprietary or customary style has a truly compelling advantage.

## Countries

Represent country names by two-character code per **ISO 3166** (https://www.iso.org).

Use the code in a table, column, or row that clearly marks it as a country.

| Code | Country |
|------|---------|
| DE | Germany |
| ES | Spain |
| FR | France |
| IT | Italy |
| JP | Japan |
| MX | Mexico |
| US | United States |

## Currency

Express currency amounts with three-letter currency code per **ISO 4217**, not symbols such as the dollar sign ($), which aren't unique and are easily misread.

**Usage:** Write amount, then a space, then currency code in capitals.

> The computer is priced at 1199 USD.
> The computer costs 1980 EUR.

| Code | Currency |
|------|----------|
| CAD | Canadian dollar |
| EUR | euro |
| GBP | pound sterling |
| JPY | yen |
| USD | U.S. dollar |

## Dates and times

Express dates as year, month, day, separated by hyphens. Express times on a 24-hour clock. Per **ISO 8601**.

**Rationale:** Largest units come first. Left to right: year, month, week, day, hour, minute, second.

**Usage:** Colon separates hours, minutes, and seconds. Express Coordinated Universal Time (UTC) times as "Z." Express local time zones as hours from UTC.

> Apple Watch Series 9 was introduced on 2023-09-12.
> The file will be posted at 18:00Z.
> The file will be posted at 18:00 PST (UTC−8).

## Decimals

Express decimals with period or comma. For numbers larger than 999, don't use period or comma as separator. A nonbreaking space (Option-Space bar) may be used instead. Per **BIPM SI Brochure** (https://www.bipm.org).

**Usage:** In English, use a period for decimals. Numbers may be split in groups of three on either side of the decimal for readability; divide them with a nonbreaking space, not a period or comma. Express large numbers in smallest form for readability.

> A kilobyte is 1024 bytes.
> Apple sold 300 000 iMac computers in the first quarter.
> Apple sold 3.7 million iMac computers in 2 years.

## Languages

Represent language names by two-character code per **ISO 639**.

| Code | Language |
|------|----------|
| de | German |
| en | English |
| es | Spanish |
| fr | French |
| it | Italian |
| jp | Japanese |
| nl | Dutch |
| mul | Multiple languages |

Sometimes append an extension to the code for a particular localization:

| Code | Language |
|------|----------|
| en-GB | British English |
| zh-CN | Simplified Chinese |
| zh-TW | Traditional Chinese |

## Telephone numbers

Telephone numbers start with plus sign, then country code, city code, and number. Express freephone (toll-free) numbers in local style. Always give a toll number if available. Per **ITU-T E.123**.

**Rationale:** Plus sign (+) stands for any outside-line prefix a caller must dial, like 9, before the remaining digits.

**Usage:** A space may mark breaks in national numbering plans.

> You can reach Apple by calling +1 408 996 1010 or 800-692-7753 (in North America).
> You can reach Apple France by calling +33 1 69 86 34 00 or 0800 046 046.

## Units of measure (international)

Express quantity values only in International System of Units (SI). Nonmetric equivalents may follow SI values in parentheses where safety may be an issue, or when used in a product's name. Per **BIPM SI Brochure**.

**Usage:** Always express quantities with a unit symbol. Put a nonbreaking space (Option-Space bar) between quantity and symbol. Unit symbols don't change in plural and are never hyphenated, even as adjectives. No period after a unit symbol unless it ends a sentence. Don't choose a unit symbol that implies more precision than reasonable.

> The Apple HDMI to HDMI Cable is 1.8 m long.
> The 13-inch MacBook Air computer weighs 1.35 kg.
> The iPad mini 4 Wi-Fi models weigh 298.8 g (0.65 lb.).
> The iMac computer has a 1.6 GHz, 2.8 GHz, or 3.1 GHz processor.

See also [units-of-measure.md](units-of-measure.md) for full SI unit table and U.S. document conventions.
