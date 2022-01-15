import json
import re
from collections import Counter
from locale import normalize
from pathlib import Path
from typing import Union

import arabic_reshaper
import matplotlib.pyplot as plt
from bidi.algorithm import get_display
from hazm import Normalizer, word_tokenize
from loguru import logger
from src.data import DATA_DIR
from src.fonts import FONT_DIR
from wordcloud import WordCloud


class ChatStatistics:

    def __init__(self, json_path: Union[str, Path]):
        """Args:
            json_path (Union[str, Path]): [path of telegram data in json file.]
        """
        # importing chat_data
        logger.info(f"loading chat data from {json_path}")
        with open(DATA_DIR / json_path) as f:
            self.chat_data = json.load(f)
        
        # creating normalizer object
        self.normalizer = Normalizer()

        # importing stop-words
        logger.info(f"importing stop words from {DATA_DIR / 'stopwords.txt'}")
        stop_words = open(DATA_DIR / 'stopwords.txt').readlines()
        stop_words = list( map(str.strip, stop_words) )
        self.stop_words = list( map(self.normalizer.normalize, stop_words) )
        
        # catching text content and statistics
        logger.info("loading text content...")
        text_content = ''
        for msg in self.chat_data['messages']:
            
            if type(msg['text']) is str:
                tokens = word_tokenize(msg['text'])
                tokens = list(filter(lambda item: item not in stop_words, tokens))
                text_content += " " + ' '.join(tokens)
            else:
                for ind in range(len(msg['text'])):
                    if type(msg['text'][ind]) is str:
                        tokens = word_tokenize(msg['text'][ind])
                        tokens = list(filter(lambda item: item not in stop_words, tokens))
                        text_content += " " + ' '.join(tokens)
                    else:
                        tokens = word_tokenize(msg['text'][ind]['text'])
                        tokens = list(filter(lambda item: item not in stop_words, tokens))
                        text_content += " " + ' '.join(tokens)

        self.text_content = text_content


    def generate_word_cloud(
        self, 
        out_put_path: Union[str, Path],
        width: int= 1200, height: int= 1200,
        max_font_size: int= 600,
        max_words: int= 400,
        ):


        self.text_content = self._removeWeirdChars(self.text_content)
        self.text_content = arabic_reshaper.reshape(self.text_content)
        
        logger.info("generating word-cloud...")
        wordcloud = WordCloud( 
            width=width, height=height,
            background_color='white', 
            font_path=str(FONT_DIR / 'NotoNaskhArabic-Regular.ttf'),
            max_font_size=max_font_size,
            max_words=max_words
            ).generate(self.text_content)
        
        logger.info(f"saving word-cloud to {out_put_path}")
        return wordcloud.to_file(str(Path(out_put_path) / 'cloud.png' ))


    def _removeWeirdChars(self, text: str):
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





if __name__ == "__main__":
    statics = ChatStatistics('riazi1.json')
    statics.generate_word_cloud(DATA_DIR)
    print('Done!')
