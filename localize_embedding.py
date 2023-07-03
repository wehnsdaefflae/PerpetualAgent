from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel


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
