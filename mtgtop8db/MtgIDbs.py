from mtgtop8db.Providers import *


class Mtgtop8Db():
    # Db parameters:

    # [format, num_of_pages] used as sources to populate the db. Can be called more than once to add sources.
    # Suggested choices are subsets of last two months' decks:
    # [['ST', 10], ['PI', 7], ['MO', 12], ['LE', 10],['VI', 3], ['cEDH', 5], ['EDH', 8], ['PAU', 6]]

    pool_list = [['ST', 10], ['PI', 7], ['MO', 12], ['LE', 10],
                 ['VI', 3], ['cEDH', 5], ['EDH', 8], ['PAU', 6]]

    # db filename, will be saved in .\data\:

    db_filename = "MtgI.db"

    # cards' data json. Needs a Scryfall json. TODO: autodownload most recent json.

    json_path = 'default-cards-20220606210607.json'

    load_cards_data = False

    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def create_or_update_db(self):

        db = SqliteProvider(self.db_filename)

        for pool in self.pool_list:
            [pool_tournaments, pool_decks,
                pool_decklists] = Mtgtop8Provider.get_mtgtop8_deckbase(*pool)
            db.save_deckbase(pool_tournaments, pool_decks, pool_decklists)
            print(f'Pool loaded: [{str(pool)}] ')

        if self.load_cards_data:
            db.save_cards_data(self.json_path)
            print(f'Cards data loaded from {self.json_path}')
        self.db = db
