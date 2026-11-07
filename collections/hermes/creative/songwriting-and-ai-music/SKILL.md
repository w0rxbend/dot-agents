---
name: songwriting-and-ai-music
description: "Songwriting craft and Suno AI music prompts. Use when the user wants lyrics, song structure help or prompts for Suno-style AI music generation."
version: 1.0.0
author: Teknium (teknium1), Hermes Agent
license: MIT
tags: [songwriting, music, suno, parody, lyrics, creative]
platforms: [linux, macos, windows]
triggers:
  - writing a song
  - song lyrics
  - music prompt
  - suno prompt
  - parody song
  - adapting a song
  - AI music generation
---

# Songwriting & AI Music Generation

Everything here is GUIDELINE, not rule. Art breaks rules on purpose.
Use what serves song. Ignore what doesn't.

---

## 1. Song Structure (Pick One or Invent Your Own)

Common skeletons — mix, modify or discard:

```
ABABCB  Verse/Chorus/Verse/Chorus/Bridge/Chorus    (most pop/rock)
AABA    Verse/Verse/Bridge/Verse (refrain-based)    (jazz standards, ballads)
ABAB    Verse/Chorus alternating                    (simple, direct)
AAA     Verse/Verse/Verse (strophic, no chorus)     (folk, storytelling)
```

Six building blocks:
- Intro      — set mood, pull listener in
- Verse      — story, details, world-building
- Pre-Chorus — optional tension ramp before payoff
- Chorus     — emotional core, part people remember
- Bridge     — detour, shift in perspective or key
- Outro      — farewell, can echo or subvert rest

Not all needed. Some great songs are one section that evolves.

---

## 2. Rhyme, Meter, and Sound

RHYME TYPES (tight to loose):
- Perfect: lean/mean
- Family: crate/braid
- Assonance: had/glass (same vowels, different endings)
- Consonance: scene/when (different vowels, similar endings)
- Near/slant: suggests connection without locking it down

Mix them. All-perfect can sound like nursery rhyme. All-slant can sound lazy.

INTERNAL RHYME: Rhyming within line, not only at ends.
  "We pruned the lies from bleeding trees / Distilled the storm
   from entropy" — "lies/flies," "trees/entropy" create internal echoes.

METER: Rhythm of stressed vs unstressed syllables.
- Match syllable counts across parallel lines for singability
- STRESSED syllables matter more than total count
- Say it aloud. If you stumble, meter needs work.
- Deliberate meter breaks create emphasis or surprise

---

## 3. Emotional Arc and Dynamics

ENERGY MAPPING (rough idea, not prescription):
  Intro: 2-3  |  Verse: 5-6  |  Pre-Chorus: 7
  Chorus: 8-9  |  Bridge: varies  |  Final Chorus: 9-10

Most powerful dynamic trick: CONTRAST.
- Whisper before scream hits harder than screaming alone
- Sparse before dense. Slow before fast. Low before high.
- Drop only works because of buildup
- Silence is an instrument

"Whisper to roar to whisper" — start intimate, build to full power,
strip back to vulnerability. Works for ballads, epics, anthems.

---

## 4. Writing Lyrics That Work

SHOW, DON'T TELL (usually):
- "I was sad" = flat
- "Your hoodie's still on the hook by the door" = alive
- But sometimes "I give my life" said plainly IS the power

THE HOOK:
- Line people remember, hum, repeat
- Usually title or core phrase
- Works best when melody + lyric + emotion align
- Place where it lands hardest (often first/last line of chorus)

PROSODY — lyrics and music supporting each other:
- Stable feelings (resolution, peace) pair with settled melodies,
  perfect rhymes, resolved chords
- Unstable feelings (longing, doubt) pair with wandering melodies,
  near-rhymes, unresolved chords
- Verse melody typically sits lower, chorus higher
- Flip this if it serves song

AVOID (unless on purpose):
- Cliches on autopilot ("heart of gold" without earning it)
- Forcing word order to hit rhyme ("Yoda-speak")
- Same energy in every section (flat dynamics)
- Treating first draft as sacred — revision is creation

---

## 5. Parody and Adaptation

When rewriting existing song with new lyrics:

THE SKELETON: Map original's structure first.
- Count syllables per line
- Mark rhyme scheme (ABAB, AABB, etc.)
- Identify STRESSED syllables
- Note where held/sustained notes fall

FITTING NEW WORDS:
- Match stressed syllables to same beats as original
- Total syllable count can flex by 1-2 unstressed syllables
- On long held notes, match original's VOWEL SOUND
  (if original holds "LOOOVE" with an "oo" vowel, "FOOOD" fits
   better than "LIFE")
- Monosyllabic swaps in key spots keep rhythm intact
  (Crime -> Code, Snake -> Noose)
- Sing new words over original — if you stumble, revise

CONCEPT:
- Pick concept strong enough to sustain whole song
- Start from title/hook, build outward
- Generate lots of raw material (puns, phrases, images) FIRST,
  then fit best into structure
- If a specific line must land somewhere, reverse-engineer
  rhyme scheme backward to set it up

KEEP SOME ORIGINALS: A few intact original lines or structures add
recognizability. Audience feels connection.

---

## 6. Suno AI Prompt Engineering

### Style/Genre Description Field

FORMULA (adapt as needed):
  Genre + Mood + Era + Instruments + Vocal Style + Production + Dynamics

```
BAD:  "sad rock song"
GOOD: "Cinematic orchestral spy thriller, 1960s Cold War era, smoky
       sultry female vocalist, big band jazz, brass section with
       trumpets and french horns, sweeping strings, minor key,
       vintage analog warmth"
```

DESCRIBE THE JOURNEY, not genre alone:
```
"Begins as a haunting whisper over sparse piano. Gradually layers
 in muted brass. Builds through the chorus with full orchestra.
 Second verse erupts with raw belting intensity. Outro strips back
 to a lone piano and a fragile whisper fading to silence."
```

TIPS:
- V4.5+ supports up to 1,000 chars in Style field — use them
- NO artist names or trademarks. Describe sound instead.
  "1960s Cold War spy thriller brass" not "James Bond style"
  "90s grunge" not "Nirvana-style"
- Specify BPM and key if you have preference
- Use Exclude Styles field for what you DON'T want
- Unexpected genre combos can be gold: "bossa nova trap",
  "Appalachian gothic", "chiptune jazz"
- Build vocal PERSONA, not only gender:
  "A weathered torch singer with a smoky alto, slight rasp,
   who starts vulnerable and builds to devastating power"

### Metatags (place in [brackets] inside lyrics field)

STRUCTURE:
  [Intro] [Verse] [Verse 1] [Pre-Chorus] [Chorus]
  [Post-Chorus] [Hook] [Bridge] [Interlude]
  [Instrumental] [Instrumental Break] [Guitar Solo]
  [Breakdown] [Build-up] [Outro] [Silence] [End]

VOCAL PERFORMANCE:
  [Whispered] [Spoken Word] [Belted] [Falsetto] [Powerful]
  [Soulful] [Raspy] [Breathy] [Smooth] [Gritty]
  [Staccato] [Legato] [Vibrato] [Melismatic]
  [Harmonies] [Choir] [Harmonized Chorus]

DYNAMICS:
  [High Energy] [Low Energy] [Building Energy] [Explosive]
  [Emotional Climax] [Gradual swell] [Orchestral swell]
  [Quiet arrangement] [Falling tension] [Slow Down]

GENDER:
  [Female Vocals] [Male Vocals]

ATMOSPHERE:
  [Melancholic] [Euphoric] [Nostalgic] [Aggressive]
  [Dreamy] [Intimate] [Dark Atmosphere]

SFX:
  [Vinyl Crackle] [Rain] [Applause] [Static] [Thunder]

Put tags in BOTH style field AND lyrics for reinforcement.
Max 5-8 tags per section — too many confuses AI.
Don't contradict yourself ([Calm] + [Aggressive] in same section).

### Custom Mode
- Always use Custom Mode for serious work (separate Style + Lyrics)
- Lyrics field limit: ~3,000 chars (~40-60 lines)
- Always add structural tags — without them Suno defaults to
  flat verse/chorus/verse with no emotional arc

---

## 7. Phonetic Tricks for AI Singers

AI vocalists don't read — they pronounce. Help them:

PHONETIC RESPELLING:
- Spell words as they SOUND: "through" -> "thru"
- Proper nouns are highest failure rate — test early
- "Nous" -> "Noose" (forces correct pronunciation)
- Hyphenate to guide syllables: "Re-search", "bio-engineering"

DELIVERY CONTROL:
- ALL CAPS = louder, more intense
- Vowel extension: "lo-o-o-ove" = sustained/melisma
- Ellipses: "I... need... you" = dramatic pauses
- Hyphenated stretch: "ne-e-ed" = emotional stretch

ALWAYS:
- Spell out numbers: "24/7" -> "twenty four seven"
- Space acronyms: "AI" -> "A I" or "A-I"
- Test proper nouns/unusual words in short 30-second clip first
- Once generated, pronunciation is baked in — fix in lyrics BEFORE

---

## 8. Workflow

1. Write concept/hook first — what's the emotional core?
2. If adapting, map original structure (syllables, rhyme, stress)
3. Generate raw material — brainstorm freely before structuring
4. Draft lyrics into structure
5. Read/sing aloud — catch stumbles, fix meter
6. Build Suno style description — paint dynamic journey
7. Add metatags to lyrics for performance direction
8. Generate 3-5 variations minimum — treat like recording takes
9. Pick best; use Extend/Continue on promising sections
10. If something great happens by accident, keep it

EXPECT: ~3-5 generations per 1 good result. Revision is normal.
Style can drift in extensions — restate genre/mood when extending.

---

## 9. Lessons Learned

- Bridge is where you can transform imagery. Swap original's specific
  references for your theme's metaphors. Keep emotional function
  (reflection, shift, revelation).
- Strong vocal persona in style field beats any single metatag.
- If a line breaks meter but hits harder, keep it. Feeling matters most.

---

## 10. Local / Open-Source Music Generation

Two optional skills cover local, GPU-based generation instead of Suno.
Heavy dependencies, so not installed by default. Each pulls third-party
code and model weights; confirm with user before installing:

- **heartmula** — full songs with vocals from lyrics + tags
  (open-source Suno alternative, 8-16GB VRAM):
  `hermes skills install official/creative/heartmula`
- **audiocraft** — Meta's MusicGen (instrumental text-to-music) and
  AudioGen (sound effects):
  `hermes skills install official/creative/audiocraft-audio-generation`

Lyric and prompt craft here applies to heartmula too. Its input:
lyrics with bracketed structure tags plus comma-separated style tags.
