# Honest Lines data

Every morning a GitHub Action re-runs the college basketball and NFL models and saves the newest pick files in `data/`. The website reads them from here, so nothing needs uploading by hand.

## What's here

| Path | What it is |
|---|---|
| `.github/workflows/update-picks.yml` | The daily job (about 9:17 AM Chicago time, plus a "Run workflow" button) |
| `notebooks/` | The same notebooks you run in Colab. The job runs these exact files |
| `scripts/run_notebook.py` | Runs a notebook top to bottom without opening it |
| `scripts/publish.py` | Checks the new files and copies them into `data/` |
| `data/` | What the website reads: picks, ratings, track record, `last_updated.json` |
| `seed/cbb_data.zip.enc.part*` | Encrypted starting copy (in 3 parts) of the college basketball history, so the first run doesn't re-download every season |

## Secrets it needs

Settings → Secrets and variables → Actions:

- `CBBD_API_KEY`: your CollegeBasketballData key (the same one as in Colab)
- `SEED_PASSWORD`: unlocks the files in `seed/`

## Day to day

- **Run it now:** Actions tab → Update picks → Run workflow.
- **If a run fails:** GitHub emails you, and the site keeps showing the last good files. Open the run and the red step to see the error.
- **If you change a notebook in Colab:** download it (File → Download .ipynb) and replace the copy in `notebooks/` with the same file name.
- **API use:** about 10 CollegeBasketballData calls per run, roughly 300 a month.

The raw game data stays in GitHub's private Actions cache and isn't published in this repository.
