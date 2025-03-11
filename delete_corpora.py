from google.oauth2 import service_account
import google.ai.generativelanguage as glm

service_account_file_name = "service_account_key.json"
credentials = service_account.Credentials.from_service_account_file(service_account_file_name)

scoped_credentials = credentials.with_scopes([
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/generative-language.retriever"
])

retriever_service_client = glm.RetrieverServiceClient(credentials=scoped_credentials)


def delete_all_corpora():
    try:
        list_corpora_request = glm.ListCorporaRequest()
        corpora_response = retriever_service_client.list_corpora(list_corpora_request)

        if not corpora_response.corpora:
            print("No corpora to delete.")
            return

        for corpus in corpora_response.corpora:
            print(f"Deleting corpus: {corpus.name}")
            delete_corpus_request = glm.DeleteCorpusRequest(name=corpus.name, force=True)
            retriever_service_client.delete_corpus(delete_corpus_request)
            print(f"Deleted corpus: {corpus.name}")

        print("All corpora deleted successfully!")

    except Exception as e:
        print(f"Error while deleting corpora: {e}")

delete_all_corpora()
