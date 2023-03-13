import telebot
import requests

#-----------------------------------------

def search_anime(title):
    prioritize_translations = '704,734,643,609,557'

    payload = {
        'token':kodik_token,
        'title':title,
        'prioritize_translations':prioritize_translations,
        'with_seasons':'true',
        'with_episodes_data':'true',
        'with_page_links':'true'
    }

    res = requests.get(url=kodik_url_search, params=payload).json()

    ind = 0

    while(ind <= len(res['results'])-2):
        ind1 = ind + 1

        while(ind1 <= len(res['results'])-1):
            if(res['results'][ind].get('title_orig') != None and res['results'][ind].get('title_orig') == res['results'][ind1].get('title_orig')):
                res['results'].pop(ind1)
            else:
                ind1 += 1
        ind += 1

    return res


def create_markup(index, count, data, url):
    markup = telebot.types.InlineKeyboardMarkup()
    key_previous = telebot.types.InlineKeyboardButton(text='⟵', callback_data='previous_'+data)

    if(data == 'season' or data == 'seria'):
        key_play= telebot.types.InlineKeyboardButton(text='{0}/{1}'.format(index+1, count), url=url)
    else:
        key_play= telebot.types.InlineKeyboardButton(text='▶', url=url)

    key_watch = telebot.types.InlineKeyboardButton(text='👀', callback_data='watch_'+data)
    key_next = telebot.types.InlineKeyboardButton(text='⟶', callback_data='next_'+data)

    if(index == 0 and index < count-1):
        markup.add(key_play, key_next)

        if(data != 'seria'):
            markup.add(key_watch)

    elif(index > 0 and index < count-1):
        markup.add(key_previous, key_play, key_next)

        if(data != 'seria'):
            markup.add(key_watch)

    elif(index > 0 and index == count-1):
        markup.add(key_previous, key_play)

        if(data != 'seria'):
            markup.add(key_watch)

    else:
        if(data != 'seria'):
            markup.add(key_watch, key_play)
        else:
            markup.add(key_play)

    return markup


def analysis_anime(chat_id):
    global res
    global anime_index

    i = anime_index[chat_id]

    anime = res[chat_id]['results'][i]
    title = anime['title']
    orig_title = anime['title_orig']
    year = anime['year']
    anime_link = anime['link']
    text = '*Название*: {0}\n*Оригинальное название*: {1}\n*Год*: {2}'.format(title, orig_title, year)

    if(anime['type'] == 'anime-serial'):
        text += '\n*Сезоны*: ' + str(len(anime['seasons']))

    markup = create_markup(i, len(res[chat_id]['results']), 'anime', anime_link)

    return text, markup


def watch_season(chat_id):
    global res
    global season_index

    index = season_index[chat_id]
    anime = res[chat_id]['results'][anime_index[chat_id]]
    seasons = []

    for key in anime['seasons']:
        seasons.append(anime['seasons'][key])

    markup = create_markup(index, len(seasons), 'season', seasons[index]['link'])
    text = '*Выбор сезона:*'

    return text, markup


def watch_seria(chat_id):
    global res
    global seria_index

    index = seria_index[chat_id]
    anime = res[chat_id]['results'][anime_index[chat_id]]
    seasons = []

    for key in anime['seasons']:
        seasons.append(anime['seasons'][key])
    season = seasons[season_index[chat_id]]
    serias = []

    for key in season['episodes']:
        serias.append(season['episodes'][key])
    markup = create_markup(index, len(serias), 'seria', serias[index])
    text = '*Выбор серии:*'

    return text, markup

#-----------------------------------------

kodik_url_search = 'https://kodikapi.com/search'
kodik_token = ''
telegram_token = ''

#-----------------------------------------

global res
global anime_index
global season_index
global seria_index
global id_message
res = dict()
anime_index = dict()
season_index = dict()
seria_index = dict()
id_message = dict()

#-----------------------------------------

bot = telebot.TeleBot(telegram_token)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text='Привет, сучЬка')

@bot.message_handler(content_types=['text'])
def send_text(message):
    global res
    global anime_index
    global season_index
    global seria_index

    chat_id = message.chat.id

    res[chat_id] = search_anime(message.text)
    print(res[chat_id])
    anime_index[chat_id] = 0
    season_index[chat_id] = 0
    seria_index[chat_id] = 0

    text, markup = analysis_anime(chat_id)
 
    id_message[chat_id] = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode="Markdown").id

@bot.callback_query_handler(func = lambda call: True)
def callback_inline(call):
    global anime_index
    global season_index
    global seria_index
    global id_message

    data = call.data
    chat_id = call.message.chat.id
    NPW = ['next_anime', 'previous_anime', 'watch_anime', 'next_season', 'previous_season', 'watch_season', 'next_seria', 'previous_seria']

    if(data in NPW):
        if(data == 'next_anime'):
            anime_index[chat_id] += 1
            text, markup = analysis_anime(chat_id)
        elif(data == 'previous_anime'):
            anime_index[chat_id] -= 1
            text, markup = analysis_anime(chat_id)
        elif(data == 'watch_anime'):
            season_index[chat_id] = 0
            seria_index[chat_id] = 0
            text, markup = watch_season(chat_id)
        elif(data == 'next_season'):
            season_index[chat_id] += 1
            text, markup = watch_season(chat_id)
        elif(data == 'previous_season'):
            season_index[chat_id] -= 1
            text, markup = watch_season(chat_id)
        elif(data == 'watch_season'):
            seria_index[chat_id] = 0
            text, markup = watch_seria(chat_id)
        elif(data == 'next_seria'):
            seria_index[chat_id] += 1
            text, markup = watch_seria(chat_id)
        elif(data == 'previous_seria'):
            seria_index[chat_id] -= 1
            text, markup = watch_seria(chat_id)

        if(data != 'watch_anime' and data != 'watch_season'):
            bot.delete_message(chat_id=chat_id, message_id=id_message[chat_id])

        id_message[chat_id] = bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode="Markdown").id
        



bot.polling(none_stop=True, interval=0)