from gensim.models import Word2Vec

model = Word2Vec.load("./word_embedding/word2vec.model")

# 计算某个词的相关词列表
y2 = model.wv.most_similar("摩加迪沙", topn=10)  # 10个最相关的
a = model.vocabulary
b=a.raw_vocab
print(b)
print(u"和区块链最相关的词有：\n")
for item in y2:
    print(item[0], item[1])
print("-------------------------------\n")
print(u"区块链词向量为：\n")
print(model.wv['区块链'])
