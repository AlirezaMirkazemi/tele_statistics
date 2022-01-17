import json
import re
from collections import Counter
from pathlib import Path
from tkinter import N
from typing import Union

import arabic_reshaper
from hazm import Normalizer, word_tokenize, sent_tokenize
from loguru import logger
from src.data import DATA_DIR
from src.fonts import FONT_DIR
from src.utils.IO import read_file
from src.utils.IO import read_json
from wordcloud import WordCloud
from collections import defaultdict, Counter


class ChatStatistics:

    def __init__(self, json_path: Union[str, Path]):
        """Args:
            json_path (Union[str, Path]): [path of telegram data in json file.]
        """
        # importing chat_data
        logger.info(f"loading chat data from {json_path}")
        self.chat_data = read_json(DATA_DIR / json_path)
        # creating normalizer object
        self.normalizer = Normalizer()
        # importing stop-words
        logger.info(f"importing stop words from {DATA_DIR / 'stopwords.txt'}")
        stop_words = read_file(DATA_DIR / 'stopwords.txt')
        stop_words = stop_words
        stop_words = map(str.strip, stop_words)
        self.stop_words = set( map(self.normalizer.normalize, stop_words) )
        self.question_tokens = self.get_question_tokens(self.chat_data['messages'])
        # catching text content and statistics
        self.text_content = self.get_text_content(self.chat_data['messages'])
        self.questions_id = self.question_id_finder(self.chat_data['messages'])
        self.clean_text = None
        self.USERS_INFO = self._generate_users_info_dictionary(self.chat_data['messages'])
        self.top_messagers = self.top_messager(len(self.USERS_INFO.keys()))
        self.top_repliers = self.top_replier(len(self.USERS_INFO.keys()))
        self.top_questioners = self.top_questioner(len(self.USERS_INFO.keys()))
        self.top_question_repliers = self.top_question_replier(len(self.USERS_INFO.keys()))

    def generate_word_cloud(
        self, 
        out_put_path: Union[str, Path],
        width: int= 1200, height: int= 1200,
        max_font_size: int= 600,
        max_words: int= 400,
        ):


        self.clean_text = self.remove_weird_chars(self.text_content)
        self.clean_text = arabic_reshaper.reshape(self.clean_text)
        
        logger.info("generating word-cloud...")
        wordcloud = WordCloud( 
            width=width, height=height,
            background_color='white', 
            font_path=str(FONT_DIR / "B Homa_0.ttf"),
            max_font_size=max_font_size,
            max_words=max_words
            ).generate(self.clean_text)
        
        logger.info(f"saving word-cloud to {out_put_path}")
        return wordcloud.to_file(str(Path(out_put_path) / 'cloud.png' ))

    def remove_weird_chars(self, text: str):
        """ommit unicodes and wierd charactors for generating word-cloud

        Args:
            text : [rough and dirty text]

        Returns:
            [str]: [cleaned text]
        """

        logger.info("remove wierd chars for generating word-cloud...")
        weirdPatterns = re.compile("["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                u"\U00002702-\U000027B0"
                                u"\U000024C2-\U0001F251"
                                u"\U0001f926-\U0001f937"
                                u'\U00010000-\U0010ffff'
                                u"\u200d"
                                u"\u2640-\u2642"
                                u"\u2600-\u2B55"
                                u"\u23cf"
                                u"\u23e9"
                                u"\u231a"
                                u"\u3030"
                                u"\ufe0f"
                                u"\u2069"
                                u"\u2066"
                                u"\u200c"
                                u"\u2068"
                                u"\u2067"
                                "]+", flags=re.UNICODE)
        return weirdPatterns.sub(r'', text)

    def get_text_content(self, dictionary: dict):
        """[summary]

        Args:
            dictionary (dict): [json dict]

        Returns:
            [str]: [text contents joined together]
        """
        logger.info("loading text content...")
        text_content = ""
        for msg in dictionary:
            repaired_text = self.repair_msg(msg['text'])
            tokens = word_tokenize(repaired_text)
            tokens = list(filter(lambda item: item not in self.stop_words, tokens))
            text_content += " " + ' '.join(tokens)
        
        return text_content

    def repair_msg(self, text_list: list):
        """repair messages which are not string

        Args:
            text_list (list): [list of messages]

        Returns:
            [str]: [repaired message]
        """
        if isinstance(text_list, str):
            return text_list
        repaired_text = ''
        for ind in range(len(text_list)):
            if type(text_list[ind]) is str:
                repaired_text += " " + text_list[ind]
            else:
                repaired_text += " " + text_list[ind]['text']    
        return repaired_text

    def get_question_tokens(self, data: list):
        """gives most common words used in questions in data

        Args:
            data (list): [telegram json chat history file]

        Returns:
            [list]: [most common words used in questions in data]
        """
        # reading question stopwordsfile
        question_stopwords = read_file(DATA_DIR / 'question_stopwords.txt')
        question_stopwords = ' '.join(question_stopwords)
        question_stopwords = question_stopwords.split(' ')
        logger.info("collecting most used words in questions...")
        question_content = ''
        for msg in data:
            text = ''
            if isinstance(msg['text'], str):
                text += ' ' + msg['text']
                text = sent_tokenize(text)
            else:
                repaired_text = self.repair_msg(msg['text'])
                text += ' ' + repaired_text

            for txt in text:
                if '?' in txt or '؟' in txt:
                    question_content += '' + txt

        question_tokens = Counter(word_tokenize(question_content)).most_common()
        question_tokens = list(filter(lambda tkn: tkn[0] not in question_stopwords, question_tokens))[0:30]
        question_tokens = [tkn[0] for tkn in question_tokens]
        
        return question_tokens

    def question_id_finder(self, data: dict):
        """find questions id in the chat

        Args:
            data (dict): [telegram json chat hoistory dict]

        Returns:
            [list]: [questions id]
        """

        questions_id = []
        for msg in data:
            repaired_text = self.repair_msg(msg['text'])
            if self.is_question(repaired_text) == True:
                questions_id.append(msg['id'])
        return questions_id

    def is_question(self, text: str):
        """[revognize if a sentence is question or not]

        Args:
            text (str): [your text]

        Returns:
            [boolian]: 
        """
        text_tkn = word_tokenize(text)
        similars = set(text_tkn) & set(self.question_tokens)
        if ('?' in similars) or ('؟' in similars):
            return True
        elif len(similars) >= 5:
            return True
        else:
            return False

    def _generate_users_info_dictionary(self, data: dict, 
    options: list=['name', 'acts_id', 'messages_id', 'replies_id', 'replies_to_id','q_asked_id','q_replied_id']):
        """generates USERS statistics info dictionary

        Args:
            data (dict): [telegran json chat hisory file]
            options (list, optional): [options that each user has]. Defaults to ['name', 'acts_id', 'messages_id', 'replies_id', 'replies_to_id','q_asked_id','q_replied_id'].

        Returns:
            [dict]: [USERS statistics info dictionary]
        """

        from_id_name = {(msg['from_id'], msg['from']) for msg in data if 'from_id' in msg.keys()}
        actor_id_name = {(msg['actor_id'], msg['actor']) for msg in data if 'actor' in msg.keys()}
        users_id_name = dict(from_id_name | actor_id_name)
        USERS = {key: defaultdict() for key in users_id_name.keys()}
        for usr in USERS.keys():
            for opt in options:
                if opt == 'name':
                    USERS[usr][opt] = users_id_name[usr]
                    continue
                USERS[usr][opt] = []

        USERS = self._assign_users_info(USERS, self.chat_data['messages'])

        return USERS

    def _assign_users_info(self, USERS: dict, data: dict):
        
        logger.info("generating users statistic info...")
        for msg in data:  
            if 'actor' in msg.keys():
                id_ = msg['actor_id']
                USERS[id_]['acts_id'].append(msg['id'])
            else:
                id_ = msg['from_id']
                USERS[id_]['messages_id'].append(msg['id'])
                
                if msg['id'] in self.questions_id:
                    USERS[id_]['q_asked_id'].append(msg['id'])
                    
                if 'reply_to_message_id' in msg.keys():
                    USERS[id_]['replies_id'].append(msg['id'])
                    USERS[id_]['replies_to_id'].append(msg['reply_to_message_id'])
                    if msg['reply_to_message_id'] in self.questions_id:
                        USERS[id_]['q_replied_id'].append(msg['reply_to_message_id'])


        return USERS

    def top_messager(self, n: int=1):
        top_n =[]
        for usr in self.USERS_INFO:
            top_n.append((len(self.USERS_INFO[usr]['messages_id']), self.USERS_INFO[usr]['name']))
        top_n = sorted(top_n, reverse=True)[:n]
        top_n = {key:value for (value, key) in top_n}
        return top_n

    def top_replier(self, n: int=1):
        top_n =[]
        for usr in self.USERS_INFO:
            top_n.append((len(self.USERS_INFO[usr]['replies_id']), self.USERS_INFO[usr]['name']))
        top_n = sorted(top_n, reverse=True)[:n]
        top_n = {key:value for (value, key) in top_n}
        return top_n

    def top_questioner(self, n: int=1):
        top_n =[]
        for usr in self.USERS_INFO:
            top_n.append((len(self.USERS_INFO[usr]['q_asked_id']), self.USERS_INFO[usr]['name']))
        top_n = sorted(top_n, reverse=True)[:n]
        top_n = {key:value for (value, key) in top_n}
        return top_n

    def top_question_replier(self, n: int=1):
        top_n =[]
        for usr in self.USERS_INFO:
            top_n.append((len(self.USERS_INFO[usr]['q_replied_id']), self.USERS_INFO[usr]['name']))
        top_n = sorted(top_n, reverse=True)[:n]
        top_n = {key:value for (value, key) in top_n}
        return top_n

if __name__ == "__main__":
    statics = ChatStatistics('riazi1.json')
    statics.generate_word_cloud(DATA_DIR)
    print(statics.top_messagers)

    print('Done!')
