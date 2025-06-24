import numpy as np
import pandas as pd
from mlxtend.frequent_patterns.apriori import apriori
from mlxtend.preprocessing import TransactionEncoder
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
import os
import codecs
from db import db
import pymorphy2 
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
stop_words = set(stopwords.words('russian'))
from joblib import dump, load

def pymorphy2_311_hotfix():
    from inspect import getfullargspec
    from pymorphy2.units.base import BaseAnalyzerUnit

    def _get_param_names_311(klass):
        if klass.__init__ is object.__init__:
            return []
        args = getfullargspec(klass.__init__).args
        return sorted(args[1:])

    setattr(BaseAnalyzerUnit, '_get_param_names', _get_param_names_311)
    
pymorphy2_311_hotfix()

class Analyzer:    
    def get_termins(feedback):
        morph = pymorphy2.MorphAnalyzer()
        termins = []
        for review in feedback:
            transaction = []
            id = review[0]
            text = review[4]
            clear_text = re.sub('[^А-Яа-яё0-9]+', ' ', text).lower()
            for sentence in nltk.sent_tokenize(clear_text, language='russian'):
                bigrams = list(nltk.bigrams(nltk.word_tokenize(sentence, language='russian')))
                for first, second in bigrams:
                    first_morphed = morph.parse(first)[0]
                    second_morphed = morph.parse(second)[0]
                    morphed = [first_morphed, second_morphed]
                    if Analyzer.__is_noun_phrase(morphed):
                        transaction.append(' '.join([morphed[0][0], morphed[1][0]]))
                    elif first_morphed.tag.POS == 'NOUN':
                        transaction.append(first_morphed.normal_form)
                if len(bigrams) > 0:
                    last_morphed = morph.parse(bigrams[len(bigrams) - 1][1])[0]
                    if last_morphed.normal_form == 'NOUN':
                        transaction.append(last_morphed.normal_form)
            for gramm in set(transaction):
                termins.append({"_id": id, "transaction": gramm})
        return termins
    
    @staticmethod
    def __is_noun_phrase(words):
        return (words[0].tag.POS == 'ADJF' and words[1].tag.POS == 'NOUN' or words[0].tag.POS == 'NOUN' and words[1].tag.POS == 'ADJF') \
               and words[0].tag.case == words[1].tag.case \
               and words[0].tag.gender == words[1].tag.gender \
               and (words[0].tag.gender == "masc" or  words[0].tag.gender == "femn")
    
    @staticmethod    
    def get_significant_termins(termins, minsup=0.02):
        transactions_for_te = []
        for doc in termins:
            transaction = doc["transaction"]
            transactions_for_te.append(transaction.split())

        te = TransactionEncoder()
        oht_ary = te.fit(transactions_for_te).transform(transactions_for_te, sparse=True)
        sparse_df = pd.DataFrame.sparse.from_spmatrix(oht_ary, columns=te.columns_)
        
        df_aspects = apriori(sparse_df, min_support=minsup, use_colnames=True, max_len=2)

        aspect_docs = []
        for i in df_aspects.index:
            aspect = ' '.join(list(df_aspects.loc[i, 'itemsets']))
            aspect_docs.append({'aspect': aspect, 'support': df_aspects.loc[i, 'support']})
        return aspect_docs
    
    @staticmethod
    def extraxt_tonal(feedback, init_aspects):
        aspects = [aspect[2] for aspect in init_aspects]
        morph = pymorphy2.MorphAnalyzer()
        window_radius = 3
        sw = set(stopwords.words('russian'))
        sw.remove('не')
        tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
        tonal = []
        for review in feedback:
            id = review[0]
            text = review[4]
            extracted_aspects = []
            for sentence in nltk.sent_tokenize(text.lower(), language='russian'):
                words = tokenizer.tokenize(sentence) 
                filtered_words = []
                for w in words:
                    if w not in sw:
                        filtered_words.append(w)
                        
                for j in range(0, len(filtered_words)):
                    morphed = morph.parse(filtered_words[j])[0]
                    index = Analyzer.__find_index(morphed.normal_form, aspects)
                    if morphed.tag.POS == 'NOUN' and index != -1:
                        Analyzer.__scan_window_for_sentiment(id, init_aspects[index][0], filtered_words, j, window_radius, morph, tonal, extracted_aspects)
                        
        return tonal
        
    @staticmethod
    def __scan_window_for_sentiment(id, asp_id, sentence_words, aspect_position, window_radius, morph, tonal, extracted_aspects):
        left_i = max(0, aspect_position - window_radius)
        right_i = min(aspect_position + window_radius, len(sentence_words) - 1)
        min_distance = 1000
        sentiment = ''
        aspect_morphed = morph.parse(sentence_words[aspect_position])[0]
        for i in range(left_i, right_i + 1):
            if i == aspect_position:
                continue
            for morphed in morph.parse(sentence_words[i])[:2]:
                if Analyzer.__are_words_consistent(morphed, aspect_morphed, i, aspect_position, min_distance):
                    min_distance = abs(i - aspect_position)
                    sentiment = morphed.normal_form
                    break
        asp = aspect_morphed.normal_form
        if sentiment != '' and asp_id not in extracted_aspects:
            tonal.append([id, asp_id, sentiment + " " + asp])
            extracted_aspects.append(asp_id)
     
        
    @staticmethod    
    def __are_words_consistent(morphed, aspect_morphed, word_position, aspect_position, min_distance):
        if (word_position - aspect_position) >= min_distance:
            return False
        pos = morphed.tag.POS
        score = 0
        if pos == 'ADJF' or pos == 'ADJS' or pos == 'PRTF':
            if morphed.tag.case == aspect_morphed.tag.case:
                score += 1
            if morphed.tag.number == aspect_morphed.tag.number:
                score += 1
            if morphed.tag.gender == aspect_morphed.tag.gender:
                score += 1
            return score >= 2
        return False

    @staticmethod
    def __find_index(element, array):
        try:
            return array.index(element)
        except ValueError:
            return -1
    
    @staticmethod
    def classify_tonality(tonality, tonal):
        df = pd.DataFrame(tonality)
        df.columns = ['value', 'tonality']
        target_df = pd.DataFrame([{'value': ton[2], 'tonality': -1} for ton in tonal ])
        df = pd.concat([df, target_df], ignore_index=True)
        text_documents = df['value'].apply(lambda x: ' '.join(word_tokenize(x.lower())))
        vectorizer = TfidfVectorizer(ngram_range=(1, 1))
        tfidf_matrix = vectorizer.fit_transform(text_documents)
        nb_classifier = MultinomialNB()
        
        nb_classifier.fit(tfidf_matrix[:-len(tonal)], df['tonality'].iloc[:-len(tonal)])
        y_pred_nb = nb_classifier.predict(tfidf_matrix[-len(tonal):])
        for i in range(len(tonal)):
            tonal[i].append(y_pred_nb[i])
        return tonal
       
    @staticmethod    
    def predict_helpfullness(feedbaack):
        df = pd.DataFrame(feedbaack)
        df.columns = ['id', 'pr_id', 'date', 'stars', 'text', 'likes', 'disslikes', 'usefullness']
        
        
        lemmatizer = WordNetLemmatizer()
        for index, text in df["text"].items():
            df.at[index, 'len'] = len(text)
            sentences = sent_tokenize(text)
            words = word_tokenize(text)
            df.at[index, 'avg_sen_len'] = len(words) / len(sentences)
            filtered_tokens = [word.lower() for word in words if word.lower() not in stop_words]
            lemmatized_tokens = [lemmatizer.lemmatize(word) for word in filtered_tokens]
            df.at[index, 'body_clean'] = " ".join(lemmatized_tokens)
            questions_count = 0
            exclamation_count = 0
            for sentence in sentences:
                if sentence.endswith('?'):
                    questions_count += 1
                elif sentence.endswith('!'):
                    exclamation_count += 1
            df.at[index, 'quest_per'] = questions_count / len(sentences) * 100
            df.at[index, 'excl_per'] = exclamation_count / len(sentences) * 100
            words_clean = word_tokenize(df.at[index, 'body_clean'])
            pos_tags = nltk.pos_tag(words)
            vb_count = 0
            noun_count = 0
            adj_count = 0
            adv_count = 0
            for _, tag in pos_tags:
                if tag.startswith('VB'):
                    vb_count += 1 
                elif tag.startswith('NN'):
                    noun_count += 1
                elif tag.startswith('JJ'):
                    adj_count += 1
                elif tag.startswith('RB'):
                    adv_count += 1
            df.at[index, 'vb_per'] = vb_count / len(words_clean) * 100
            df.at[index, 'nn_per'] = noun_count / len(words_clean) * 100
            df.at[index, 'adj_per'] = adj_count / len(words_clean) * 100
            df.at[index, 'adv_per'] = adv_count / len(words_clean) * 100
            df.at[index, 'asp_count'] = db.select_aspects_count(df.at[index, 'id'])
            
        df = df.drop(["text", "body_clean", "likes", "disslikes", "date", "pr_id", "usefullness", "id"], axis=1)
        scaler = StandardScaler()
        numerical_features = ['stars', 'avg_sen_len', 'quest_per', 'excl_per', 'vb_per', 'nn_per', 'adj_per', 'adv_per', 'asp_count']
        df_norm = df.copy()
        df_norm[numerical_features] = scaler.fit_transform(df_norm[numerical_features])
        model_rf =  load('helpfullness_model.joblib')
        result = model_rf.predict(df_norm)
        return result
