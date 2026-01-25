import itad_client as ic
import private_data
import pandas as pd


def find_and_delete_user_notes(note_text):
    # get user notes
    user_notes = ic.GetUserNotes().df

    # # show unique user notes
    # unique_notes = list(dict.fromkeys(get_user_notes.df['note']))

    # filter games with certain notes & delete this notes
    filtered_notes = user_notes[user_notes['note']
                                == note_text]
    ic.DeleteUserNotesFromGame(filtered_notes['game_id'].to_list())

    urls = ic.BaseClass.get_games_url(filtered_notes['game_id'].to_list())
    filtered_notes.insert(2, 'url', urls)
    ic.print_tit(f'Deleted notes where note is \'{note_text}\'')
    print(filtered_notes[['game_id',
                          'note',
                          'url']])


def get_copies_and_shops_for_collection():
    copies = ic.GetCopiesOfGames().df
    coll = ic.GetGamesFromCollection().df

    games_without_copies = pd.merge(coll,
                                    copies,
                                    on='game_id',
                                    how='left_anti')
    urls = ic.BaseClass.get_games_url(
        games_without_copies['game_id'].to_list())
    games_without_copies.insert(2, 'url', urls)
    ic.print_tit('games in collection without copies')
    print(games_without_copies[['game_id',
                                'game_title',
                                'url',
                                'game_type']])

    copies_with_name = pd.merge(coll,
                                copies,
                                on='game_id')
    ic.print_tit('games in collection with copies ')
    print(copies_with_name[['game_id',
                            'game_title',
                            'copy_id']])

    is_copy_dup = copies.duplicated(subset=['game_id'],
                                    keep=False)
    dup_copies = copies_with_name[is_copy_dup]
    urls = ic.BaseClass.get_games_url(dup_copies['game_id'].to_list())
    dup_copies.insert(2, 'url', urls)
    ic.print_tit('duplicate copies')
    print(dup_copies[['game_id',
                      'game_title',
                      'copy_id',
                      'shop_name',
                      'url',
                      'game_type']])
    print(len(dup_copies))

    pass


# ==================== Main ====================
if __name__ == '__main__':
    pd.set_option('display.max_colwidth',  None)

    ic.BaseClass.get_access_token(api_key=private_data.API_KEY,
                                  client_id=private_data.CLIENT_ID,
                                  client_secret=private_data.CLIENT_SECRET)

    find_and_delete_user_notes('Tengo en Epic')
    find_and_delete_user_notes('Tengo en GOG')
    find_and_delete_user_notes('Tengo en Ubisoft Connect')
    find_and_delete_user_notes('Tengo en EA App')
