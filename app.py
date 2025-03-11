import tkinter as tk
from tkinter import filedialog, scrolledtext
from langchain_community.document_loaders import PyPDFLoader
from google.oauth2 import service_account
import google.ai.generativelanguage as glm

service_account_file_name = "service_account_key.json"
credentials = service_account.Credentials.from_service_account_file(service_account_file_name)
scoped_credentials = credentials.with_scopes([
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/generative-language.retriever"
])

generative_service_client = glm.GenerativeServiceClient(credentials=scoped_credentials)
retriever_service_client = glm.RetrieverServiceClient(credentials=scoped_credentials)


def create_corpus(display_name):
    example_corpus = glm.Corpus(display_name=display_name)
    create_corpus_request = glm.CreateCorpusRequest(corpus=example_corpus)
    create_corpus_response = retriever_service_client.create_corpus(create_corpus_request)
    return create_corpus_response.name


def create_document(corpus_resource_name, display_name):
    example_document = glm.Document(display_name=display_name)
    create_document_request = glm.CreateDocumentRequest(parent=corpus_resource_name, document=example_document)
    create_document_response = retriever_service_client.create_document(create_document_request)
    return create_document_response.name


def chunk_text_by_length(text, max_length=2000):
    chunks = []
    current_chunk = ""
    for sentence in text.split(". "):
        if len(current_chunk) + len(sentence) + 1 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
        else:
            current_chunk += sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def add_chunks_to_document(document_resource_name, chunks):
    for index, chunk_text in enumerate(chunks):
        chunk = glm.Chunk(data={"string_value": chunk_text})
        chunk_request = glm.CreateChunkRequest(parent=document_resource_name, chunk=chunk)
        retriever_service_client.create_chunk(chunk_request)


def generate_answer(corpus_resource_name, user_query, answer_style="ABSTRACTIVE", model_name="models/aqa"):
    content = glm.Content(parts=[glm.Part(text=user_query)])
    retriever_config = glm.SemanticRetrieverConfig(source=corpus_resource_name, query=content)
    req = glm.GenerateAnswerRequest(
        model=model_name,
        contents=[content],
        semantic_retriever=retriever_config,
        answer_style=answer_style
    )
    aqa_response = generative_service_client.generate_answer(req)
    return aqa_response


class PDFQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Query System")

        self.label = tk.Label(root, text="Upload a PDF and enter your query:")
        self.label.pack(pady=10)

        self.upload_button = tk.Button(root, text="Upload PDF", command=self.upload_pdf)
        self.upload_button.pack(pady=5)

        self.query_label = tk.Label(root, text="Enter your query:")
        self.query_label.pack(pady=5)

        self.query_entry = tk.Entry(root, width=50)
        self.query_entry.pack(pady=5)

        self.submit_button = tk.Button(root, text="Submit Query", command=self.submit_query)
        self.submit_button.pack(pady=10)

        self.response_box = scrolledtext.ScrolledText(root, width=60, height=20, wrap=tk.WORD)
        self.response_box.pack(pady=10)

        self.pdf_text = ""
        self.corpus_resource_name = ""
        self.document_resource_name = ""

    def upload_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            self.pdf_text = " ".join([doc.page_content for doc in documents])
            self.response_box.insert(tk.END, "PDF uploaded successfully. Ready for querying.\n")

    def submit_query(self):
        user_query = self.query_entry.get()
        if not self.pdf_text or not user_query:
            self.response_box.insert(tk.END, "Please upload a PDF and enter a query first.\n")
            return

        try:
            if not self.corpus_resource_name:
                self.response_box.insert(tk.END, "Processing the PDF...\n")
                chunks = chunk_text_by_length(self.pdf_text, max_length=2000)
                self.corpus_resource_name = create_corpus("Local PDF Corpus")
                self.document_resource_name = create_document(self.corpus_resource_name, "Uploaded PDF")
                add_chunks_to_document(self.document_resource_name, chunks)

            self.response_box.insert(tk.END, "Generating response...\n")
            aqa_response = generate_answer(self.corpus_resource_name, user_query, answer_style="ABSTRACTIVE")
            answer = aqa_response.answer.content.parts[0].text
            self.response_box.insert(tk.END, f"Query: {user_query}\nAnswer: {answer}\n\n")
        except Exception as e:
            self.response_box.insert(tk.END, f"Error: {e}\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFQueryApp(root)
    root.mainloop()
