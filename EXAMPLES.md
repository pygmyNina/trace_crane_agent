# Training Examples

Real examples of training interactions and use cases.

## Example 1: Index Format Training

### Question
```
What does =61/102.8 expand to in full format?
```

### Student Answer
```
=61/102.8.0
```

### AI Feedback
```
Not quite! The shorthand =61/102.8 actually expands to =61/102.0.8

Explanation: In shorthand notation, when the sheet minor digit (.Y) is 0,
it can be omitted. The missing part is the sheet minor digit, not an
additional column digit.

The format is =XX/YY.Y.Z where:
- XX = Section (61)
- YY.Y = Sheet (102.0)
- Z = Column (8)

So =61/102.8 is shorthand for =61/102.0.8
```

### Logged Correction
- **Category**: index_format
- **Incorrect**: =61/102.8.0
- **Correct**: =61/102.0.8
- **Note**: Student confused which digit is omitted in shorthand

---

## Example 2: Wire Tracing

### Question
```
Looking at this schematic, are wires A and B connected if they cross
perpendicularly without a dot at the intersection?
```

### Student Answer
```
Yes, they are connected because they touch
```

### AI Feedback
```
That's incorrect. When two wires cross perpendicularly (at 90 degrees)
WITHOUT a dot at the crossing point, they are NOT connected.

Key Rule: Only connections with dots are actual electrical connections.
Perpendicular crossings without dots indicate the wires pass over/under
each other without connecting.

Think of it like a highway overpass - two roads can cross but traffic
doesn't mix unless there's an interchange (the dot).
```

### Logged Correction
- **Category**: wire_tracing
- **Incorrect**: Yes, connected
- **Correct**: No, not connected
- **Note**: Must have dot for connection

---

## Example 3: Slave Sequence

### Question
```
If we have Slave 23, what is the NEXT slave in the sequence?
```

### Student Answer
```
Slave 24
```

### AI Feedback
```
That's incorrect! The slave sequence is non-chronological.

The correct sequence is: 22, 23, 60, 24, 61, 20

After Slave 23, the next slave is Slave 60, not Slave 24.

This is a common mistake - never assume slaves are numbered sequentially!
```

### Logged Correction
- **Category**: slave_sequence
- **Incorrect**: 24
- **Correct**: 60
- **Note**: Sequence is 22,23,60,24,61,20

---

## Example 4: Module Counting

### Question
```
Slave 22 is in Cabinet E11. How many total modules does it have?
```

### Student Answer
```
44
```

### AI Feedback
```
Close, but not quite! Slave 22 has 45 modules total, not 44.

The breakdown is:
- 1 IM151 (Interface Module)
- 1 PM (Power Module)
- 40 DI (Digital Input modules)
- 3 RTD (RTD modules)

Total: 1 + 1 + 40 + 3 = 45 modules

Make sure to count all module types when calculating the total!
```

### Logged Correction
- **Category**: module_counting
- **Incorrect**: 44
- **Correct**: 45
- **Note**: Miscounted modules

---

## Example 5: Component Location

### Question
```
Where is component HVC3 located in the schematic?
```

### Student Answer
```
=10/103.7
```

### AI Feedback
```
Very close! HVC3 is at =10/103.0.7, not =10/103.7

Remember:
- =10/103.7 (shorthand) = =10/103.0.7 (full)
- Your answer is correct in shorthand form!

Both notations refer to the same location:
- Section: 10
- Sheet: 103.0
- Column: 7

Well done! You found the right location.
```

### Logged Correction
- **Category**: notation
- **Incorrect**: =10/103.7 (missing expansion context)
- **Correct**: =10/103.0.7
- **Note**: Correct in shorthand, show both forms

---

## Example 6: Quiz Session

### Complete Quiz Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     QUIZ MODE - 5 Questions                  │
└─────────────────────────────────────────────────────────────┘

Q1: What section is the Main Transformer located in?
    Your answer: 10
    ✓ Correct! Main Transformer is at =10/102.0.3

Q2: In the slave sequence 22,23,60,24,61,20, what comes after 60?
    Your answer: 61
    ✗ Incorrect. After 60 comes 24, then 61.

Q3: Does a perpendicular wire crossing WITH a dot indicate a connection?
    Your answer: Yes
    ✓ Correct! Dots indicate electrical connections.

Q4: What does =61/102.8 expand to?
    Your answer: =61/102.0.8
    ✓ Correct! You understand shorthand notation.

Q5: How many DI modules does Slave 22 have?
    Your answer: 40
    ✓ Correct! Slave 22 has 40 DI modules.

┌─────────────────────────────────────────────────────────────┐
│                       QUIZ RESULTS                           │
│                                                              │
│  Score: 4/5 (80%)                                           │
│  Correct: 4                                                 │
│  Incorrect: 1                                               │
│                                                              │
│  Area for improvement: Slave Sequence                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Example 7: Category Practice - Index Format

### Practice Session

```
┌─────────────────────────────────────────────────────────────┐
│         Practice: Index Format Interpretation                │
└─────────────────────────────────────────────────────────────┘

[AI Trainer]: Let's practice index format. I'll give you several
notation examples.

Question 1: What is the section number in =45/201.5.3?
Your answer: 45
[AI Trainer]: ✓ Correct! Section is the first two digits (XX).

Question 2: What is the full sheet number in =45/201.5.3?
Your answer: 201.5
[AI Trainer]: ✓ Correct! Sheet is YY.Y format.

Question 3: If I write =30/150.2, what's the full format?
Your answer: =30/150.2.0
[AI Trainer]: ✗ Not quite. When you see two digits after the slash
followed by a decimal and one digit (YY.Z), that's shorthand.
The full format is =30/150.0.2

The pattern is:
- =XX/YY.Y.Z (full)
- =XX/YY.Z (shorthand, implies .0 in the middle)

Let's try another...
```

---

## Example 8: PDF-Based Training

### Training with Actual Schematic

```
┌─────────────────────────────────────────────────────────────┐
│         PDF Loaded: crane_schematic_01.pdf                   │
│         Pages: 45                                            │
└─────────────────────────────────────────────────────────────┘

[AI Trainer]: I've analyzed page 1 of your schematic. I found 12
index references and 8 components.

Let me ask you about what's on this page:

Question: I see component HVC1 on this page. What index reference
appears closest to it in the schematic?

Your answer: =10/102.0.5
[AI Trainer]: Let me check... Yes! That's correct. HVC1 is near
=10/102.0.5 on this page.

Next question: On the same page, I see three wires labeled W1, W2,
and W3. Do W1 and W2 connect based on the schematic?

[Student examines PDF and answers...]
```

---

## Example 9: Correction Review

### Reviewing Past Mistakes

```
┌─────────────────────────────────────────────────────────────┐
│              Session Corrections - session_20251023_143022   │
└─────────────────────────────────────────────────────────────┘

Correction 1
  Category: index_format
  Question: What does =61/102.8 expand to?
  Your answer: =61/102.8.0
  Correct: =61/102.0.8
  Note: Shorthand omits middle digit (.Y), not end digit

Correction 2
  Category: wire_tracing
  Question: Are perpendicular wires without dots connected?
  Your answer: Yes
  Correct: No
  Note: Only dots indicate connections

Correction 3
  Category: slave_sequence
  Question: What comes after Slave 23?
  Your answer: 24
  Correct: 60
  Note: Sequence is non-chronological: 22,23,60,24,61,20

┌─────────────────────────────────────────────────────────────┐
│                     RECOMMENDATIONS                          │
│                                                              │
│  Focus Areas:                                               │
│  1. Index format shorthand rules                            │
│  2. Wire connection identification                          │
│  3. Slave sequence memorization                             │
│                                                              │
│  Suggested Practice:                                        │
│  - Review foundation knowledge on index format              │
│  - Practice with wire_tracing category                      │
│  - Quiz yourself on slave sequence                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Example 10: Progress Tracking

### Statistics View

```
┌─────────────────────────────────────────────────────────────┐
│              Performance by Category                         │
└─────────────────────────────────────────────────────────────┘

Category                    Total  Correct  Incorrect  Accuracy
────────────────────────────────────────────────────────────────
Index Format                  25      22        3       88.0%
Wire Tracing                  18      15        3       83.3%
Component Identification      12      11        1       91.7%
Slave Sequence                 8       5        3       62.5%  ⚠
Module Counting                6       6        0      100.0%  ✓
Notation                      15      14        1       93.3%
Location                       9       8        1       88.9%

Overall: 93/103 = 90.3%

⚠ Recommendation: Focus on Slave Sequence (62.5% accuracy)
✓ Excellent: Module Counting (100% accuracy)
```

---

These examples demonstrate the various training scenarios and how the
system provides feedback, tracks progress, and helps learners improve
their crane schematic reading skills.
