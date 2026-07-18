import os
import sys
import glob
import logging
import PyPDF2
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("DataIngest")

class RecursiveCharacterTextSplitter:
    """
    Splits text recursively by character separators to preserve paragraphs,
    sentences, and words, ensuring chunks fit within the requested chunk_size.
    """
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        if not separators:
            # Hard limit split if no separators remain
            chunks = []
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunks.append(text[start:end])
                start += self.chunk_size - self.chunk_overlap
            return chunks

        separator = separators[0]
        next_separators = separators[1:]

        # Split by the current separator
        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)

        chunks = []
        current_doc = []
        total_len = 0

        for split in splits:
            # If a single piece is larger than chunk_size, split it recursively
            if len(split) > self.chunk_size:
                if current_doc:
                    chunks.append(separator.join(current_doc))
                    current_doc = []
                    total_len = 0
                chunks.extend(self._split_text(split, next_separators))
            else:
                # Add current split
                add_len = len(split) + (len(separator) if current_doc else 0)
                if total_len + add_len > self.chunk_size:
                    # Current chunk is full
                    if current_doc:
                        chunks.append(separator.join(current_doc))
                    
                    # Backtrack to build the overlapping slice
                    overlap_doc = []
                    overlap_len = 0
                    for s in reversed(current_doc):
                        s_len = len(s) + (len(separator) if overlap_doc else 0)
                        if overlap_len + s_len <= self.chunk_overlap:
                            overlap_doc.insert(0, s)
                            overlap_len += s_len
                        else:
                            break
                    current_doc = overlap_doc
                    total_len = overlap_len
                    add_len = len(split) + (len(separator) if current_doc else 0)

                current_doc.append(split)
                total_len += add_len

        if current_doc:
            chunks.append(separator.join(current_doc))

        return chunks

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        logger.error(f"Error reading PDF file {file_path}: {e}")
    return text

def extract_text(file_path: str) -> str:
    """Directs text extraction based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in [".txt", ".md"]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                return f.read()
    elif ext == ".pdf":
        return extract_text_from_pdf(file_path)
    return ""

def main():
    logger.info("Initializing RAG Ingestion Pipeline...")
    
    # 1. Ensure sys.path includes the current directory to import backend modules
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # 2. Import RAG search components
    try:
        from app.rag.search import HybridSearch
        logger.info("Successfully imported backend Search engine.")
        # Instantiate searcher to connect to ChromaDB and load embeddings model
        searcher = HybridSearch(corpus=[])
    except Exception as e:
        logger.error(f"Failed to load backend search components: {e}", exc_info=True)
        sys.exit(1)

    if not searcher.chroma_collection:
        logger.error("ChromaDB is not initialized or unavailable. Ingestion cannot proceed.")
        sys.exit(1)

    # 3. Handle data folder setup and discovery
    kb_dir = "./knowledge_base"
    if not os.path.exists(kb_dir):
        os.makedirs(kb_dir)
        logger.info(f"Created folder '{kb_dir}'. Place documents there to ingest.")
        
    supported_extensions = ["*.txt", "*.md", "*.pdf"]
    discovered_files = []
    for ext in supported_extensions:
        discovered_files.extend(glob.glob(os.path.join(kb_dir, "**", ext), recursive=True))

    if not discovered_files:
        logger.warning(f"No documents (.txt, .md, .pdf) found in '{kb_dir}'. Exiting.")
        print("\n" + "="*60)
        print(" INGESTION PIPELINE FINISHED: 0 files processed, 0 vectors written.")
        print("="*60 + "\n")
        return

    logger.info(f"Discovered {len(discovered_files)} files for ingestion.")

    # 4. Text splitting config
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    # Accumulate all vectors for batch writing
    all_ids = []
    all_embeddings = []
    all_documents = []
    all_metadatas = []
    processed_count = 0

    # 5. Process files
    for file_path in discovered_files:
        filename = os.path.basename(file_path)
        logger.info(f"Processing: {filename}")
        
        text = extract_text(file_path)
        if not text.strip():
            logger.warning(f"Skipping empty file: {filename}")
            continue

        chunks = splitter.split_text(text)
        if not chunks:
            logger.warning(f"No valid text chunks generated from {filename}")
            continue

        logger.info(f"Split {filename} into {len(chunks)} chunks.")

        # Clean existing entries from the collection for this file to avoid duplicates
        try:
            searcher.chroma_collection.delete(where={"source": filename})
            logger.info(f"Cleared existing database chunks for {filename}")
        except Exception as e:
            logger.warning(f"Could not check/clear existing chunks for {filename}: {e}")

        # Compute embeddings and build upsert payloads
        for i, chunk in enumerate(chunks):
            # Compute embeddings using standard embedding utility
            vector = searcher._get_embedding(chunk)
            
            chunk_id = f"{filename}_chunk_{i}"
            metadata = {
                "source": filename,
                "chunk_index": i,
                "title": filename.replace("_", " ").split(".")[0].title()
            }
            
            all_ids.append(chunk_id)
            all_embeddings.append(vector)
            all_documents.append(chunk)
            all_metadatas.append(metadata)

        processed_count += 1

    # 6. Batch upsert to ChromaDB
    if all_documents:
        logger.info(f"Writing {len(all_documents)} chunks to ChromaDB...")
        batch_size = 100
        for i in range(0, len(all_documents), batch_size):
            end_idx = i + batch_size
            searcher.chroma_collection.upsert(
                ids=all_ids[i:end_idx],
                embeddings=all_embeddings[i:end_idx],
                documents=all_documents[i:end_idx],
                metadatas=all_metadatas[i:end_idx]
            )
        
        logger.info("Disk write complete.")

    # 7. Print final CLI logging output
    print("\n" + "="*70)
    print("                      RAG INGESTION PIPELINE REPORT")
    print("="*70)
    print(f"  Status:             SUCCESS")
    print(f"  Knowledge Base:     {os.path.abspath(kb_dir)}")
    print(f"  Files Discovered:   {len(discovered_files)}")
    print(f"  Files Processed:    {processed_count}")
    print(f"  Total Chunk Chunks: {len(all_documents)}")
    print(f"  Vectors Written:    {len(all_embeddings)}")
    print(f"  Embedding Model:    all-MiniLM-L6-v2 (384 Dimensions)")
    print(f"  Chroma Directory:   {os.environ.get('CHROMA_DB_DIR', './chroma_data')}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
