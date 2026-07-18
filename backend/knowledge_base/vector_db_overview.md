# Vector Database Systems and ChromaDB

Vector databases are purpose-built storage systems designed to handle high-dimensional vector embeddings efficiently.
Unlike relational databases or traditional document stores, vector databases index data based on mathematical similarity rather than exact keywords or key-value constraints.

## Persistent Storage with ChromaDB

ChromaDB is an open-source embedding database tailored for AI applications and agentic workflows.
It can run in-memory, inside a Docker container, or as a persistent local database saved directly to the file system.

### Key Operations
1. **Embedding Models**: Sentence-transformers (such as `all-MiniLM-L6-v2`) generate dense vectors of 384 dimensions from raw text segments.
2. **Indexing**: HNSW (Hierarchical Navigable Small World) graphs are constructed to allow low-latency approximate nearest neighbor (ANN) searches.
3. **Filtering**: ChromaDB supports metadata filtration keys like `source` or `technology` to narrow down results before or after computing semantic relevance.

This system guarantees that search indices can scale and remain consistent on local disks.
