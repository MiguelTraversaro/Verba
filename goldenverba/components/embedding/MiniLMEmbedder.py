from weaviate import Client
from wasabi import msg

from tqdm import tqdm

from goldenverba.components.embedding.interface import Embedder
from goldenverba.components.reader.document import Document


class MiniLMEmbedder(Embedder):
    """
    MiniLMEmbedder for Verba
    """

    def __init__(self):
        super().__init__()
        self.name = "MiniLMEmbedder"
        self.requires_library = ["torch", "transformers"]
        self.description = "Embeds and retrieves objects using SentenceTransformer's all-MiniLM-L6-v2 model"
        self.vectorizer = "MiniLM"
        self.model = None
        self.tokenizer = None
        try:
            from transformers import AutoTokenizer, AutoModel

            self.model = AutoModel.from_pretrained(
                "sentence-transformers/all-MiniLM-L6-v2"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                "sentence-transformers/all-MiniLM-L6-v2"
            )

        except:
            pass

    def embed(
        self,
        documents: list[Document],
        client: Client,
    ) -> bool:
        """Embed verba documents and its chunks to Weaviate
        @parameter: documents : list[Document] - List of Verba documents
        @parameter: client : Client - Weaviate Client
        @parameter: batch_size : int - Batch Size of Input
        @returns bool - Bool whether the embedding what successful
        """

        for document in tqdm(
            documents, total=len(documents), desc="Vectorizing document chunks"
        ):
            for chunk in document.chunks:
                chunk.set_vector(self.vectorize_chunk(chunk.text))

        return self.import_data(documents, client)

    def vectorize_chunk(self, chunk) -> list[float]:
        try:
            import torch

            text = chunk
            tokens = self.tokenizer.tokenize(text)

            max_length = (
                self.tokenizer.model_max_length
            )  # Get the max sequence length for the model
            batches = []
            batch = []
            token_count = 0

            for token in tokens:
                token_length = len(
                    self.tokenizer.encode(token, add_special_tokens=False)
                )
                if token_count + token_length <= max_length:
                    batch.append(token)
                    token_count += token_length
                else:
                    batches.append(" ".join(batch))
                    batch = [token]
                    token_count = token_length

            # Don't forget to add the last batch
            if batch:
                batches.append(" ".join(batch))

            embeddings = []

            for batch in batches:
                inputs = self.tokenizer(
                    batch, return_tensors="pt", padding=True, truncation=True
                )
                with torch.no_grad():
                    outputs = self.model(**inputs)
                # Taking the mean of the hidden states to obtain an embedding for the batch
                embedding = outputs.last_hidden_state.mean(dim=1)
                embeddings.append(embedding)

            # Concatenate the embeddings to make averaging easier
            all_embeddings = torch.cat(embeddings)

            averaged_embedding = all_embeddings.mean(dim=0)

            averaged_embedding_list = averaged_embedding.tolist()

            return averaged_embedding_list

        except Exception as e:
            print(e)
            return []

    def vectorize_query(self, query: str) -> list[float]:
        return self.vectorize_chunk(query)