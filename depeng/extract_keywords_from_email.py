from depeng import read_email

from sklearn.feature_extraction.text import CountVectorizer

from sklearn.feature_extraction.text import TfidfTransformer

import re
import string

from depeng.read_email import extract
from depeng.read_email import get_email_body_from_directory

# preprocess our data
def pre_process(txt):
    # tranfer to lower case
    txt = txt.lower()
    #remove text in square brackets
    txt = re.sub('\[.*?\]', '', txt)
    # remove special characters and digital number
    txt = re.sub('\w*\d\w*', '', txt)
    #remove punctuation
    txt = re.sub('[%s]' %re.escape(string.punctuation), '', txt)
    return txt


# creating vocabulary and word counts for idf
# stopwords
def get_stop_words(stop_file):
    with open(stop_file, 'r', encoding='utf-8') as f:
        spwords = f.readlines()
        stop_set = set(m.strip() for m in spwords)
        return frozenset(stop_set)


# sort items
def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)


# extract n-top keywords
def extra_n_top_keywords(feature_names, sorted_tfidf_vector, n_top=10):
    sorted_tfidf_vector = sorted_tfidf_vector[:n_top]

    score_vals = []
    feature_vals = []

    # word index and its correspoding tf-idf score
    for idx, score in sorted_tfidf_vector:
        score_vals.append(round(score, 3))
        feature_vals.append(feature_names[idx])

    results = {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]] = score_vals[idx]

    return results

def extract_keywords(target_file, docs_path, topn,stop_file):
    data = get_email_body_from_directory(path=docs_path)
    # preprocess ducuments data
    for key, value in data.items():
        data[key] = pre_process(value)
    # get all files content in a list
    docs = [data[x] for x in data]
    # read bytes
    with open(target_file, 'rb') as tf:
        target_doc = str(extract(tf, tf.name))
    tf.close()
    stopwords = get_stop_words(stop_file)
    # create voucabulary words
    # ignore words that appear in 90% of documents
    # our vocabulary size set to 1000
    # remove stop wprds
    cv = CountVectorizer(max_df=0.90, stop_words=stopwords, max_features=1000)
    word_count = cv.fit_transform(docs)

    # list words in our vocabulary
    # print(list(cv.vocabulary_.keys())[:1000])

    # tfidf
    tfidf_transformer = TfidfTransformer(smooth_idf=True, use_idf=True)
    tfidf_transformer.fit(word_count)

    # get feature names
    feature_names = cv.get_feature_names()
    # generate tf-idf value for the given file
    tf_idf_vector = tfidf_transformer.transform(cv.transform([target_doc]))

    # sort the tf-idf vectors by descending order of scores
    sorted_tfidf_vector = sort_coo(tf_idf_vector.tocoo())

    keywords = extra_n_top_keywords(feature_names, sorted_tfidf_vector, topn)
    return keywords


if __name__ == "__main__":
    print("Let's start our work")
    docs_path = "../../spam"
    target_file = "../../spam/b'2'.eml"
    stop_file = "../depeng/resources/stopwords.txt"
    topn = 10
    keywords = extract_keywords(target_file,docs_path,topn,stop_file)
    print("Top ", topn, "keywords ")
    for word in keywords:
        print(word," ",keywords[word])

