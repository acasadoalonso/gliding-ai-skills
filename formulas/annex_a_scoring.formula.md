# FAI SC3 Annex A — Scoring and Penalties



# Part 8 — Scoring and Penalties

## Introduction to Scoring Options

Paragraphs 8.1 through 8.4 describe the **"Classic"** scoring system. In 2019, IGC approved an alternative scoring system at the discretion of the Organisers. The key difference:

- **Classic system:** awards distance points to all competitors and speed points to finishers.
- **Alternative system:** awards distance points **or** speed points — but not both — to all competitors.

The rules for Alternative Scoring can be found in the IGC document *"Alternative Scoring – Gliding"*, where paragraphs 8.1–8.4 replace the corresponding paragraphs below.

---

## 8.1 Scoring System

The Organisers shall state in the Local Procedures which Scoring System (**Classic** or **Alternative**) will be used for each class. Because classes are scored independently in a multiclass championships, both systems may be in use at a single event.

### 8.1.1 Scoring Software
The Organisers shall state in the Local Procedures the name and version number of the program to be used for scoring, and a checksum or hash of the scoring algorithm in use shall be included with the published daily results. During the competition, the Organisers must brief Team Captains about any changes to the scoring algorithm before they are put into effect.

### 8.1.2 Team Cup
This may be used concurrently for a secondary ranking, but not to select the individual Champions.

---

## 8.2 Common Rules

### 8.2.1 Championship Day

In order for a Day to be counted as a Championship Day in any class:

a. For each class, a launch opportunity shall have been given to each competitor in time to carry out the task of the Day in question, **and**

b. For each class, more than **25%** of the competitors who have had a competition launch on that Day shall have flown a credited distance (Dh) of at least **Dm × H**.

> *Dm* is defined in para. 8.3.1. *H* is defined in para. 8.3.2.
> In this Annex, "valid competition day" is synonymous with "Championship Day."

### 8.2.2 Daily Scores
Each competitor shall be given a daily Score based on their performance on each Championship Day. The Score shall be rounded to the nearest whole number, with 0.5 rounded up.

### 8.2.3 Finisher
A competitor is deemed to be a **"finisher"** if they cross the finish line or enter the finish ring after completing the task.

### 8.2.4 Handicaps
Handicapping shall be used in the **Club Class** and may be used in the **20 Metre Multi-seat Class** in Continental Gliding Championships only (not in World Gliding Championships). Organisers shall state in the CGC Local Procedures if Handicapping is to be used in the 20 Metre Multi-seat Class.

a. Handicaps shall be taken from the valid IGC Handicap list or any other list approved by the IGC Bureau for the specific Championships.

b. The Organisers shall publish a list of all competitors with their handicaps before the beginning of the Championships.

c. Handicaps shall be applied according to 8.3.2.

### 8.2.5 Penalties
Flights that have been disqualified shall be given a zero Score for the Day, but shall be counted in the scoring formula. Any penalties shall be deducted from the competitor's Score after it has been calculated.

- If the penalty reduces a competitor's raw performance for the day (e.g. outlanded at the point of airspace entry), the penalty must be applied **before** the calculation of the Score.
- The appropriate penalty should be applied each time an infringement occurs.
- If the Day score after deduction of any penalties is less than zero, it shall be taken as zero, unless 8.6.6 applies.

### 8.2.6 Cumulative Scores
Cumulative and Final Scores shall be calculated by adding the points obtained each Day.

---

## 8.3 Definitions of Scoring Parameters

> In the following tables the abbreviations **RT**, **AAT**, and **DHT** are used for Racing Task, Assigned Area Task, and Distance Handicap Task, respectively.

### 8.3.1 Championship Day Parameters

| Symbol | Definition |
|--------|------------|
| **Dt** | Task Distance *(used in scoring RT only; defined in 6.3.1c)* |
| **Td** | Minimum Task Time (hours). For AAT, Td is specified at Briefing; for RT, Td = 0 |
| **D1** | Minimum Distance for 1000 points, by class (see table below) |
| **Dm** | Minimum Distance to validate the Day, by class (see table below) |
| **n1** | Number of competitors achieving a Handicapped Distance (Dh) ≥ Dm |
| **n2** | Number of finishers exceeding 2/3 of best Handicapped Speed (Vo) |
| **n3** | Number of finishers, regardless of speed |
| **n4** | Number of competitors achieving a Handicapped Distance (Dh) ≥ Dm/2 |
| **N** | Number of competitors having had a competition launch that Day |
| **Do** | Highest Handicapped Distance (Dh) of the Day |
| **Vo** | Highest finisher's Handicapped Speed (Vh) of the Day |
| **To** | Marking Time (T) of the finisher whose Vh = Vo. In case of tie, lowest T applies. If no finishers, To = 100 |
| **Pm** | Maximum available Score for the Day, before F and FCR are applied |
| **Pdm** | Maximum available Distance Points for the Day, before F and FCR are applied |
| **Pvm** | Maximum available Speed Points for the Day, before F and FCR are applied |
| **F** | Day Factor |
| **FCR** | Completion Ratio Factor |
| **Day** | If not a Championship Day (see 8.2.1), all Scores = 0, subject to penalties in 8.2.5 |

**D1 by class:**

| Class | D1 |
|-------|----|
| 13.5 Metre, Club | 250 km |
| Standard, 15 Metre, 20 Metre Multi-seat | 300 km |
| 18 Metre, Open | 350 km |

**Dm by class:**

| Class | Dm |
|-------|----|
| 13.5 Metre, Club | 100 km |
| Standard, 15 Metre, 20 Metre Multi-seat | 120 km |
| 18 Metre, Open | 140 km |

### 8.3.2 Competitor Parameters

| Symbol | Definition |
|--------|------------|
| **D** | Competitor's Marking Distance *(defined in 6.3.1 for RT and 6.3.2 for AAT)* |
| **H** | Competitor's Handicap if handicapping is used; otherwise H = 1 |
| **Dh** | Competitor's Handicapped Distance: `Dh = D / H` |
| **T** | Finisher's Marking Time (hours) *(defined in 6.3.1 for RT and 6.3.2 for AAT)* |
| **Pd** | Competitor's Distance Points |
| **V** | Finisher's Marking Speed: `V = D / T` |
| **Vh** | Finisher's Handicapped Speed: `Vh = V / H` |
| **Pv** | Finisher's Speed Points |
| **S** | Competitor's Score for the Day (in points) |

> **Note for Scorers:** Before closure of the finish line, in order to keep preliminary results representative, it shall be presumed that competitors not accounted for are finishers, with Dh ≥ Dm and Vh = Vo, but they shall not appear in the ranking.

---

## 8.4 Calculation of Scores

### 8.4.1 Racing Task (RT) or Distance Handicap Task (DHT)

**a. Day Parameters:**

```
Pm  = least of:  1000  |  1250 × (Do/D1) − 250  |  (400 × To) − 200
F   = lesser of 1 and (1.25 × n1 / N)
FCR = lesser of 1 and (1.2 × (n2/n1) + 0.6)
Pvm = 2/3 × (n2 / N) × Pm
Pdm = Pm − Pvm
```

**b. Competitor's Score:**

**(i) For any finisher:**
```
Pv = Pvm × (Vh − 2/3 Vo) / (1/3 Vo)
Pd = Pdm
Exception: If Vh < 2/3 Vo, then Pv = 0
```

**(ii) For any non-finisher:**
```
Pv = 0
Pd = Pdm × (Dh / Do)
```

**(iii) Final Score:**
```
S = F × FCR × (Pv + Pd)
```

---

### 8.4.2 Assigned Area Task (AAT)

**a. Day Parameters:**

```
Pm  = least of:  1000  |  1250 × (Do/D1) − 250  |  (400 × To) − 200
F   = lesser of 1 and (1.25 × n1 / N)
FCR = lesser of 1 and (1.2 × (n2/n1) + 0.6)
Pvm = 2/3 × (n2 / N) × Pm
Pdm = Pm − Pvm
```

**b. Competitor's Score:**

**(i) For any finisher:**
```
Pv = Pvm × (Vh − 2/3 Vo) / (1/3 Vo)
Pd = Pdm
Exception: If Vh < 2/3 Vo, then Pv = 0
```

**(ii) For any non-finisher:**
```
Pv = 0
Pd = Pdm × (Dh / Do)
```

**(iii) Final Score:**
```
S = F × FCR × (Pv + Pd)
```
