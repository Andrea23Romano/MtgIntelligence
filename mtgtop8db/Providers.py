import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sqlite3


class Mtgtop8Provider():

    def _request_content(url):

        html_page = requests.get(url)
        try:
            html_page.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(e)
        return BeautifulSoup(html_page.content, 'html.parser')

    def get_tournaments_from_format(requested_format, pages=1) -> list:
        page_number = 1
        tournaments = []
        format_meta_dict = {'ST': 58, 'PI': 191, 'MO': 44,
                            'LE': 16, 'VI': 14, 'PAU': 110, 'cEDH': 240, 'EDH': 56}
        while page_number <= pages:
            content_soup = Mtgtop8Provider._request_content(
                f'http://mtgtop8.com/format?f={requested_format}&meta={str(format_meta_dict[requested_format])}&cp={str(page_number)}')

            tournament_link_elements = content_soup.find_all(
                href=re.compile('event'))

            for element in tournament_link_elements:
                tournament_date = None

                if element.parent.parent.find('td', {'class': 'S12'}):
                    tournament_date = element.parent.parent.find(
                        'td', {'class': 'S12'}).text
                if len(re.findall(r'\d{2,}', element['href'])) > 0:
                    tournament_id = re.findall(r'\d{2,}', element['href'])[0]
                    tournaments.append(
                        [tournament_id, tournament_date, element.contents[0], requested_format])

            page_number += 1
        tournaments_corrected = []
        for id in {x[0] for x in tournaments}:
            same_id = [x for x in tournaments if x[0] == id]

            if len(same_id) > 1:
                tournaments_corrected.append([
                    same_id[0][0], same_id[0][1], same_id[1][2]+' '+same_id[0][2], same_id[0][3]])
            elif len(same_id) == 1:
                tournaments_corrected.append(same_id[0])
        return tournaments_corrected

    def get_decks_from_tournament(tournament_id, tournament_format):

        tournament_soup = Mtgtop8Provider._request_content(
            f'http://mtgtop8.com/event?e={str(tournament_id)}&f={tournament_format}')

        deck_elements = tournament_soup.find_all(href=re.compile('d='))

        tournament_decks = []

        for element in deck_elements:
            if element.parent.parent.find('div',  'S14') and element.text != '' and element.text != 'Switch to Visual':
                tournament_decks.append(
                    (re.findall('d=\d+', element['href'])[0].replace('d=', ''), element.text, tournament_id))
        return list(set(tournament_decks))

    def get_mtgtop8_decklist(deck_id):

        deck_html = requests.get(
            f'https://www.mtgtop8.com/mtgo?d={str(deck_id)}')

        deck_lines = deck_html.text.split('\r\n')[:-1]
        if len(deck_lines) == 0:
            return []

        if 'Sideboard' in deck_lines:
            sideboard_index = deck_lines.index('Sideboard')
            mainboard = [[deck_id, int(x.split(' ', maxsplit=1)[0]), 0, x.split(' ', maxsplit=1)[1]]
                         for x in deck_lines[:sideboard_index]]
            sideboard = [[deck_id, 0, int(x.split(' ', maxsplit=1)[0]), x.split(' ', maxsplit=1)[1]]
                         for x in deck_lines[(sideboard_index+1):]]
            decklist = mainboard+sideboard
        else:
            decklist = [[deck_id, int(x.split(' ', maxsplit=1)[0]), 0, x.split(' ', maxsplit=1)[1]]
                        for x in deck_lines]
        return decklist

    def get_mtgtop8_deckbase(format, pages):

        tournaments = Mtgtop8Provider.get_tournaments_from_format(
            format, pages)

        decks_from_tournaments = [Mtgtop8Provider.get_decks_from_tournament(
            x[0], format) for x in tournaments]
        decks_flattened = [
            item for sublist in decks_from_tournaments for item in sublist]

        decklists = [Mtgtop8Provider.get_mtgtop8_decklist(deck_id) for deck_id in [
            x[0] for x in decks_flattened]]
        decklists_flattened = [
            item for sublist in decklists for item in sublist]

        decks_df = pd.DataFrame(
            decks_flattened, columns=['deck_id', 'archetype', 'tournament_id'])
        tournaments_df = pd.DataFrame(
            tournaments, columns=['tournament_id', 'date', 'name', 'format'])
        tournaments_df.dropna(subset=['date'], inplace=True)
        decklists_df = pd.DataFrame(decklists_flattened, columns=[
                                    'deck_id', 'main_count', 'side_count', 'card_name'])

        return [tournaments_df, decks_df, decklists_df]


class CardsDataProvider():

    def extract_faces(cardDataframe):
        addedFaces = pd.DataFrame()
        for index, row in cardDataframe.iterrows():
            if isinstance(row['card_faces'], list):
                for face in row['card_faces']:
                    newface = pd.DataFrame.from_dict(
                        face, orient='index').transpose()
                    if isinstance(row['colors'], list):
                        newface['colors'] = ','.join(row['colors'])
                    if isinstance(row['color_identity'], list):
                        newface['color_identity'] = ','.join(
                            row['color_identity'])
                    if isinstance(row['keywords'], list):
                        newface['keywords'] = ','.join(row['keywords'])
                    if isinstance(row['produced_mana'], list):
                        newface['produced_mana'] = ','.join(
                            row['produced_mana'])
                    addedFaces = addedFaces.append(newface, ignore_index=True)
        cardDataframe.drop(
            cardDataframe[cardDataframe['card_faces'].notnull()].index, inplace=True)
        defacedDataframe = cardDataframe.append(addedFaces, ignore_index=True)
        return defacedDataframe

    def __init__(self, json_path) -> None:

        with open(json_path, 'r', encoding='utf-8') as json_cards:
            cards_data_df = pd.read_json(json_cards)
        cards_data_df = cards_data_df[cards_data_df['multiverse_ids'].map(
            lambda d: len(d)) > 0]
        cards_data_df = CardsDataProvider.extract_faces(cards_data_df)
        cards_data_df = cards_data_df[['id', 'name', 'released_at', 'mana_cost', 'cmc', 'type_line',
                                       'oracle_text', 'power', 'toughness', 'colors', 'color_identity', 'keywords', 'legalities',
                                       'set', 'rarity', 'flavor_text', 'produced_mana', 'loyalty']]
        cards_data_df = pd.concat([cards_data_df.drop(['legalities'], axis=1),
                                   cards_data_df['legalities'].apply(pd.Series)], axis=1)
        cards_data_df['color_identity'] = [
            ','.join(x) for x in cards_data_df['color_identity']]
        cards_data_df['colors'] = [','.join(x)
                                   for x in cards_data_df['colors']]
        cards_data_df['keywords'] = [
            ','.join(x) for x in cards_data_df['keywords']]
        cards_data_df['produced_mana'] = [
            ','.join(x) if isinstance(x, list) else None for x in cards_data_df['produced_mana']]

        cards_data_df.rename(
            columns={'set': 'set_acronym', 'id': 'scryfall_id'}, inplace=True)
        cards_data_df.dropna(axis=1, how='all', inplace=True)

        self.cards_data = cards_data_df


class SqliteProvider():

    def __init__(self, filename) -> None:

        dir_name = os.path.dirname(__file__)
        data_path = os.path.join(dir_name, 'data')
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)
        db_path = os.path.join(data_path, filename)

        self.conn = sqlite3.connect(db_path)
        cur = self.conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS Tournaments (
            tournament_id INTEGER,
            date TEXT,
            name TEXT,
            format TEXT
        );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS Decks (
            deck_id INTEGER,
            archetype TEXT,
            tournament_id TEXT
            );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS Decklists (
            deck_id INTEGER,
            main_count INTEGER,
            side_count INTEGER,
            card_name TEXT
            );
        ''')
        cur.execute('''CREATE TABLE IF NOT EXISTS CardsData (
            scryfall_id TEXT,
            name TEXT,
            released_at TEXT,
            mana_cost TEXT,
            cmc INTEGER,
            type_line TEXT,
            oracle_text TEXT,
            power TEXT,
            toughness TEXT,
            colors TEXT,
            color_identity TEXT,
            keywords TEXT,
            set_acronym TEXT,
            rarity TEXT,
            flavor_text TEXT,
            produced_mana TEXT,
            loyalty INTEGER,
            eur REAL,
            eur_foil REAL,
            tix REAL,
            usd REAL,
            usd_etched REAL,
            usd_foil REAL,
            alchemy TEXT,
            brawl TEXT,
            commander TEXT,
            duel TEXT,
            explorer TEXT,
            future TEXT,
            gladiator TEXT,
            historic TEXT,
            historicbrawl TEXT,
            legacy TEXT,
            modern TEXT,
            oldschool TEXT,
            pauper TEXT,
            paupercommander TEXT,
            penny TEXT,
            pioneer TEXT,
            premodern TEXT,
            standard TEXT,
            vintage TEXT
            );''')
        self.cur = cur
        self.conn.commit()

    def save_deckbase(self, tournaments, decks, decklists):

        known_values = pd.read_sql('''SELECT t.tournament_id, d.deck_id
            FROM Tournaments t
            INNER JOIN Decks d on t.tournament_id=d.tournament_id
            ''', self.conn)

        new_tournaments = tournaments[~tournaments['tournament_id'].isin(
            known_values['tournament_id'])]
        new_decks = decks[~decks['deck_id'].isin(known_values['deck_id'])]
        new_decklists = decklists[decklists['deck_id'].isin(
            new_decks['deck_id'])]
        new_tournaments.to_sql('Tournaments', self.conn,
                               if_exists='append', index=False)
        new_decks.to_sql('Decks', self.conn, if_exists='append', index=False)
        new_decklists.to_sql('Decklists', self.conn,
                             if_exists='append', index=False)
        self.conn.commit()

    def save_cards_data(self, json):
        known_values = pd.read_sql('''SELECT name
            FROM CardsData
            ''', self.conn)
        cards_data = CardsDataProvider(
            json_path=os.path.join(self.data_path, json)).cards_data
        new_cards = cards_data[~cards_data['name'].isin(known_values)]
        new_cards.to_sql('CardsData', self.conn,
                         if_exists='append', index=False)
        self.conn.commit()

    def close_connection(self):

        self.conn.close()
