import logging
import multiprocessing
import os.path
import sys

from gensim.models import Word2Vec
from gensim.models.word2vec import PathLineSentences

if __name__ == '__main__':
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    input_dir = './cuttext'
    outp1 = 'word2vec.model'
    outp2 = 'word2vec.kv'
    fileNames = os.listdir(input_dir)
    model = Word2Vec(PathLineSentences(input_dir), size=256, window=10, min_count=5,
                     workers=multiprocessing.cpu_count(), iter=10)
    model.save(outp1)
    model.wv.save_word2vec_format(outp2, binary=False)