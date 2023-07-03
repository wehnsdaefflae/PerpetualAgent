# coding=utf-8
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel


# https://huggingface.co/spaces/mteb/leaderboard
# https://www.sbert.net/

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

model = SentenceTransformer("ggrn/e5-small-v2")
embedding_numpy = model.encode(["Hello, my dog is cute."])
embedding = embedding_numpy.tolist()
print(embedding)

tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-small")
model = AutoModel.from_pretrained("intfloat/e5-small")
tokens = tokenizer("Hello, my dog is cute", return_tensors="pt")
outputs = model(**tokens)
embedding_a = outputs.pooler_output.tolist()
print(embedding_a)
