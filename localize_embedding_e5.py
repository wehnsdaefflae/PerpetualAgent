from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-small")

model = AutoModel.from_pretrained("intfloat/e5-small")

tokens = tokenizer("Hello, my dog is cute", return_tensors="pt")

outputs = model(**tokens)

print(outputs.pooler_output.tolist())
