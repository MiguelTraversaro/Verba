import glob
from datetime import datetime
import base64
import json

import requests

from pathlib import Path
from wasabi import msg

import os

from goldenverba.components.reader.interface import Reader, InputForm
from goldenverba.components.reader.document import Document


class GithubReader(Reader):
    """
    GithubReader for Verba
    """

    def __init__(self):
        super().__init__()
        self.name = "GithubReader"
        self.requires_env = ["GITHUB_TOKEN"]
        self.description = "Downloads text files from a github repository. Use this format {owner}/{repo}/{folder}"
        self.input_form = InputForm.INPUT.value

    def load(
        self,
        bytes: list[str] = [],
        contents: list[str] = [],
        paths: list[str] = [],
        fileNames: list[str] = [],
        document_type: str = "Documentation",
    ) -> list[Document]:
        """Ingest data into Weaviate
        @parameter: bytes : list[str] - List of bytes
        @parameter: contents : list[str] - List of string content
        @parameter: paths : list[str] - List of paths to files
        @parameter: fileNames : list[str] - List of file names
        @parameter: document_type : str - Document type
        @returns list[str] - List of strings
        """

        documents = []

        # If paths exist
        if len(paths) > 0:
            for path in paths:
                if path != "":
                    files = self.fetch_docs(path)

                    for _file in files:
                        content, link, _path = self.download_file(path, _file)

                        if ".json" in _file:
                            json_obj = json.loads(str(content))
                            try:
                                document = Document.from_json(json_obj)
                            except Exception as e:
                                raise Exception(f"Loading JSON failed {e}")

                        else:
                            document = Document(
                                text=content,
                                type=document_type,
                                name=_file,
                                link=link,
                                path=_path,
                                timestamp=str(
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                ),
                                reader=self.name,
                            )
                        documents.append(document)

        msg.good(f"Loaded {len(documents)} documents")
        return documents

    def fetch_docs(self, path) -> list:
        """Fetch filenames from Github
        @parameter owner : str - Repo owner
        @parameter repo : str - Repo name
        @parameter folder_path : str - Directory in repo to fetch from
        @parameter token : str - Github token
        @returns list - List of document names
        """

        split = path.split("/")
        owner = split[0]
        repo = split[1]
        folder_path = ""
        if len(split) > 2:
            folder_path = "/".join(split[2:])

        # Path should be owner/repo
        url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN', '')}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        files = [
            item["path"]
            for item in response.json()["tree"]
            if item["path"].startswith(folder_path)
            and (
                item["path"].endswith(".md")
                or item["path"].endswith(".mdx")
                or item["path"].endswith(".txt")
                or item["path"].endswith(".json")
            )
        ]
        msg.info(
            f"Fetched {len(files)} filenames from {url} (checking folder {folder_path})"
        )
        return files

    def download_file(self, path, file_path) -> str:
        """Download files from Github based on filename
        @parameter owner : str - Repo owner
        @parameter repo : str - Repo name
        @parameter file_path : str - Path of the file in repo
        @parameter token : str - Github token
        @returns str - Content of the file
        """
        split = path.split("/")
        owner = split[0]
        repo = split[1]

        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        headers = {
            "Authorization": f"token {os.environ.get('GITHUB_TOKEN', '')}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        content_b64 = response.json()["content"]
        link = response.json()["html_url"]
        path = response.json()["path"]
        content = base64.b64decode(content_b64).decode("utf-8")
        msg.info(f"Downloaded {url}")
        return (content, link, path)