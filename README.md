# ⚽ Moneyball FC

Moneyball FC is a football scouting analysis built on StatsBomb Open Data for
Serie A 2015/16. It turns raw match events into per-player season statistics and uses them to find a replacement for a departing striker.

![Streamlit app](https://img.shields.io/badge/built%20with-Streamlit-ff4b4b)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)

## What the app does

> In summer 2016, Napoli lost Gonzalo Higuaín to Juventus after his record season. Using Serie A 2015/16 data, the app helps a scouting analyst answer, **which players make a high attacking contribution per 90 minutes, have a profile close to Higuaín's, and is that contribution sustainable or just luck?**

The app has three pages:

| Page | What you can do |
|------|-----------------|
| **Overview** (`pages/overview.py`) | The research question, headline numbers, a goals-vs-xG chart of the whole league with the shortlist highlighted, and the shortlist table. |
| **Player profile** (`pages/player_profile.py`) | Pick an attacking player: key numbers, percentile bars against the same position group, and the finishing simulation (is his goal total skill or luck?). |
| **Scouting** (`pages/scouting.py`) | Pick a target player: the most similar attacking players, a radar chart to compare up to four of them, and their metric values. |

A slider in the sidebar sets the minimum minutes played (900 by default) for every page.

### How the analysis works

The analysis answers three sub-questions:

| Sub-question | Method |
|--------------|--------|
| **SQ1 Finishing**: who scores more or fewer goals than his chances predict, and is the gap more than luck? | Each non-penalty shot is replayed 10,000 times as a coin flip that succeeds with probability = its xG. If the real goal total is outside the 5-95% range of the simulated seasons, luck alone is unlikely. |
| **SQ2 Output**: who creates and takes the best chances per 90 minutes? | Season totals divided by minutes × 90, then a percentile (0-100) within the player's position group (MID, WING, FWD). |
| **SQ3 Replacement**: whose style is closest to Higuaín's? | Eight per-90 style metrics are standardised (z-scores) and compared with cosine similarity: 1 = same profile shape, 0 = unrelated. |

The main rules:

- **Minutes played** come from the lineup files: the sum of a player's position spells,
  where an open spell lasts until the final whistle.
- **Per-90 values** are only computed for players with at least 900 minutes
  (about 10 full matches), because rates over a few hundred minutes are mostly noise.
- **npxG** (non-penalty expected goals) leaves out penalties; **xA** gives the passer the
  xG of the shot his pass created.
- **Progressive action**: a completed pass or carry that starts at x ≥ 40 and ends at most
  75% as far from the goal as it started.

All thresholds, metric lists and position groups live in one place,
[`moneyball/config.py`](moneyball/config.py), so they are easy to change.

## Data source

**[StatsBomb Open Data](https://github.com/statsbomb/open-data)**: free event-level
football data in JSON, read from
`https://raw.githubusercontent.com/statsbomb/open-data/master/data/`.
- **`data/raw/`**: a local cache of the downloaded JSON files, so each file is downloaded
  only once.
- **`data/processed/`**: four Parquet tables built by `scripts/build_dataset.py` and read by
  the notebook and the app: `matches`, `events`, `appearances` (minutes per player per
  match) and `player_season` (one row per player).

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
| `matplotlib` | radars and other pitch charts |
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

3. Download the season and build the Parquet tables:

   ```bash
   python scripts/build_dataset.py
   ```

   The first run downloads ~1.2 GB into `data/raw/` (about 8-10 minutes on a typical
   connection); later runs read the cache and take under 2 minutes. For a quick test use
   `python scripts/build_dataset.py --max-matches 20`. A match that fails to download is
   logged and skipped.

## Run

Start the web app:

```bash
streamlit run app.py
```

The browser opens at <http://localhost:8501>. Use the sidebar to move between pages.
If the Parquet tables are missing, the app shows the command to build them.

### The example notebook

[`notebooks/moneyball_walkthrough.ipynb`](notebooks/moneyball_walkthrough.ipynb) tells the
whole analysis step by step: the business question, one match downloaded and flattened,
minutes played and the goal check, then SQ1, SQ2 and SQ3 with their charts, the insights,
the shortlist and the limitations. Every computation is a call to the `moneyball` package.
Build the dataset first, then start Jupyter from the project folder and open it:

```bash
jupyter lab
```

## Project structure

```
moneyball-fc/
├── app.py                  # Streamlit entry point: declares the pages and the sidebar
├── ui_common.py            # cached data access shared by the pages
├── pages/
│   ├── overview.py         # question, headline numbers, goals vs xG, shortlist
│   ├── player_profile.py   # key numbers, percentiles (SQ2), finishing simulation (SQ1)
│   └── scouting.py         # similar players and radar comparison (SQ3)
├── moneyball/              # the backend package
│   ├── __init__.py
│   ├── config.py           # constants: data source, paths, thresholds, positions, colours
│   ├── data_loader.py      # StatsBombClient (cache, timeout, StatsBombError), load_tables
│   ├── processing.py       # flatten matches and events, minutes played, goal check
│   ├── metrics.py          # shot geometry, progressive actions, player-season table, per-90
│   ├── analysis.py         # SQ1 Monte Carlo, SQ2 percentiles, SQ3 similarity
│   └── plots.py            # charts with matplotlib and plotly
├── scripts/
│   └── build_dataset.py    # download + process the season, write the Parquet tables
├── notebooks/
│   └── moneyball_walkthrough.ipynb  # the full analysis, step by step
├── data/
│   ├── raw/                # JSON cache (gitignored)
│   └── processed/          # Parquet tables (gitignored)
├── .streamlit/config.toml  # colours of the app
├── .gitignore
├── requirements.txt
└── README.md
```

Everything in `moneyball/` is plain Python that can be reused in a notebook or a script,
while `app.py`, `ui_common.py` and `pages/` only deal with showing things on screen.
Data flows one way: `data_loader → processing → metrics → analysis / plots`.
