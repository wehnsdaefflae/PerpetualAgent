# coding=utf-8
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel


# https://huggingface.co/spaces/mteb/leaderboard
# https://www.sbert.net/

sentence_a = "Hello, my dog is cute."
sentence_b = "Hello, my dog is vicious."

# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer("ggrn/e5-small-v2")
embedding_a_numpy = model.encode([sentence_a])
embedding_b_numpy = model.encode([sentence_b])

embedding_a = embedding_a_numpy.tolist()
embedding_b = embedding_b_numpy.tolist()

print(embedding_a_numpy.dot(embedding_b_numpy.T))

exit()
tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-small")
model = AutoModel.from_pretrained("intfloat/e5-small")
tokens = tokenizer("Hello, my dog is cute", return_tensors="pt")
outputs = model(**tokens)
embedding_a = outputs.pooler_output.tolist()
print(embedding_a)
