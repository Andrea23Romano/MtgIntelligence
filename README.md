# MtGIntelligence
## Python utilities for MtG data science projects

### `mtgtop8db`
Full Mtg data processing, from scraping to storage.
`mtgtop8db` scrapes decks from [Mtgtop8](https://www.mtgtop8.com/), imports cards data from a [Scryfall](https://scryfall.com/) "bulk data" json and saves them to a Sqlite db with default path `/data/MtgI.db`.
Scraping paramenters can be found in `MtgiDbs.py`. The db can be built by running `main.py`.

---
## What's next:

- Additional functionalities for `mtgtop8db`: add decks from different sources, load your own deck, simpler cards' data retrieval.
- Jupyter notebooks: basic MtG card pool statistics, format reports, decks' trends.
- Jupyter notebooks: KNN classifier for deck's archetype
- MtgILands: a manabase recommendation model for MtG
- (for fun, much simpler than MtgILands) LandsNLP: solves a MINLP (Mixed Integer Non Linear Programming) problem, suggesting the best produced colors' profile for a given deck, under format constraint. Optimization follows seminal Frank Karsten [manabase article](https://strategy.channelfireball.com/all-strategy/mtg/channelmagic-articles/how-many-colored-mana-sources-do-you-need-to-consistently-cast-your-spells-a-guilds-of-ravnica-update/) and Teryor [update](https://gist.github.com/teryror/881d60e08480a56043895d3bbb83c374#file-mulligans-and-mana-bases-md) 






