Moneyball FC is a football scouting analysis built on StatsBomb Open Data for
Serie A 2015/16. It turns raw match events into per-player season statistics and uses them to find a replacement for a departing striker.

## Research question

> In summer 2016, Napoli lost Gonzalo Higuaín to Juventus after his record season.
> Using Serie A 2015/16 data, **which players make a high attacking contribution
> per 90 minutes, have a profile close to Higuaín's, and is that contribution
> sustainable or just luck?**

| Sub-question | Method |
|--------------|--------|
| **SQ1 – Finishing**: who scores more or fewer goals than expected (goals vs. npxG), and is the gap beyond luck? | Monte Carlo simulation |
| **SQ2 – Output**: who creates and finishes the best chances per 90, compared with players in the same position? | Per-90 metrics + percentiles |
| **SQ3 – Replacement**: whose statistical profile is closest to Higuaín's? | Standardised vectors + cosine similarity |

**Scope:** Serie A (`competition_id = 12`), season 2015/16 (`season_id = 27`),
all 380 matches. Target player for SQ3: Gonzalo Higuaín.

## Data source

**[StatsBomb Open Data](https://github.com/statsbomb/open-data)**: free event-level
football data in JSON, read from
`https://raw.githubusercontent.com/statsbomb/open-data/master/data/`.
The full season data are downloaded on demand and cached in `data/raw/` (gitignored).

### Data dictionary

Fields used in the analysis, based on Verona–Bologna (`events/3879608.json`,
3,733 events). The pitch is 120 × 80, and the attacking team always attacks
towards `x = 120`, where the goal spans `y = 36` to `44`.

| File | Field | Meaning |
|------|-------|---------|
| events | `type.name` | Event type: `Pass`, `Shot`, `Carry`, `Substitution`… |
| events | `period`, `minute`, `second` | Match clock (the second half starts at 45:00) |
| events | `team.name`, `player.name`, `position.name` | Who performed the event (missing for team events such as `Half Start`) |
| events | `location` | `[x, y]` where the event happened |
| events | `shot.statsbomb_xg` | Probability (0–1) that the shot is scored |
| events | `shot.outcome.name` | `Goal`, `Saved`, `Off T`, `Blocked`… |
| events | `shot.type.name` | `Open Play`, `Penalty`… (penalties are excluded for npxG) |
| events | `shot.key_pass_id` | ID of the pass that set up the shot |
| events | `pass.outcome.name` | **Missing means the pass was completed** |
| events | `pass.end_location` | `[x, y]` where the pass ended |
| lineups | `player_id`, `player_name` | Player identity, same IDs as in events |
| lineups | `positions[].from`, `.to` | Time in each position as `"mm:ss"`; `to = None` means until the final whistle |

## Libraries

| Library | Used for |
|---------|----------|
| `requests` | downloading the StatsBomb JSON files |
| `pandas` | flattening events and building the player-season table |
| `pyarrow` | reading and writing Parquet files |
| `numpy` | shot geometry and Monte Carlo simulation |
| `scipy` | percentiles and statistics |
| `matplotlib`, `mplsoccer` | shot maps, radars and other pitch charts |
| `plotly` | interactive charts |
| `streamlit` | the web application |
| `jupyterlab` | the notebooks |

Exact versions are listed in [`requirements.txt`](requirements.txt).

## Setup

1. Clone the repository and enter the folder:

   ```bash
   git clone https://github.com/quanghung304/moneyball-fc.git
   cd moneyball-fc
   ```

2. Create a virtual environment and install the dependencies (Python 3.12 or newer):

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Project structure

```
moneyball-fc/
├── moneyball/
│   └── __init__.py
├── notebooks/
│   └── 01_exploration.ipynb  # scratch notebook
├── .gitignore
├── requirements.txt
└── README.md
```
