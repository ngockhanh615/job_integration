from sentence_transformers import SentenceTransformer
sentences = "Cô giáo đang ăn kem"

model = SentenceTransformer('keepitreal/vietnamese-sbert')
embeddings = model.encode(sentences)
print(embeddings)
