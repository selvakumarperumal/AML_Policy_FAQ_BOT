import os
from langchain_community.document_loaders import (
    TextLoader, PyPDFLoader, UnstructuredWordDocumentLoader, 
    UnstructuredHTMLLoader, JSONLoader, CSVLoader, 
    UnstructuredExcelLoader, UnstructuredEmailLoader, 
    UnstructuredPowerPointLoader, UnstructuredEPubLoader, 
    UnstructuredXMLLoader
)
from tempfile import NamedTemporaryFile
import shutil
from typing import List
from fastapi import UploadFile
from langchain_core.documents import Document
# Removed unused import

async def read_uploaded_file(file_path: str):
    """
    Reads the content of an uploaded file based on its format.

    Args:
        file_path (str): The path to the uploaded file.

    Returns:
        str: The content of the file as a string.
    """

    # Ensure file_path is a string
    file_path = str(file_path)
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    print(f"Reading file: {file_path}, Extension: {file_extension}")

    loader_mapping = {
        '.txt': TextLoader,
        '.pdf': PyPDFLoader,
        '.docx': UnstructuredWordDocumentLoader,
        '.md': TextLoader,
        '.html': UnstructuredHTMLLoader,
        '.json': JSONLoader,
        '.csv': CSVLoader,
        '.xlsx': UnstructuredExcelLoader,
        '.xls': UnstructuredExcelLoader,
        '.eml': UnstructuredEmailLoader,
        '.pptx': UnstructuredPowerPointLoader,
        '.epub': UnstructuredEPubLoader,    
        '.xml': UnstructuredXMLLoader,
        '.rst': TextLoader,
        '.log': TextLoader,
        '.sql': TextLoader,
        '.ini': TextLoader,
        '.cfg': TextLoader
    }

    if file_extension not in loader_mapping:
        raise ValueError(f"Unsupported file format: {file_extension}")

    loader_class = loader_mapping[file_extension]
    loader = loader_class(file_path)

    try:
        documents = loader.load()
    except Exception as e:
        raise RuntimeError(f"Error loading file {file_path}: {e}")

    # Combine all documents into a single string
    try:
        content = "\n".join(doc.page_content for doc in documents if isinstance(doc, Document) and hasattr(doc, 'page_content'))
    except Exception as e:
        raise RuntimeError(f"Error processing content from file {file_path}: {e}")

    return content  


async def read_list_of_files(file_paths: List[str]) -> str:
    """
    Reads the content of multiple uploaded files.

    Args:
        file_paths (list): A list of paths to the uploaded files.

    Returns:
        str: The combined content of all files as a string.
    """

    contents = []
    for file_path in file_paths:
        try:
            content = await read_uploaded_file(file_path)
            contents.append(content)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return "\n\n".join(contents)

async def store_and_process_files(files: List[UploadFile]) -> str:
    """
    Stores uploaded files temporarily and processes their content.

    Args:
        files (list): A list of uploaded files.

    Returns:
        str: The combined content of all files as a string.
    """
    file_temporary_paths: List[str] = []
    try:
        for file in files:
            suffix = "." + (file.filename.split('.')[-1] if file.filename else "tmp")
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
                print(f"Temporary file created at: {tmp_path}")
                file_temporary_paths.append(tmp_path)

        # Process the temporarily stored files
        file_contents = await read_list_of_files(file_temporary_paths)
        return file_contents
    finally:
        # Clean up temporary files
        for tmp_path in file_temporary_paths:
            try:
                os.remove(tmp_path)
                print(f"Temporary file deleted: {tmp_path}")
            except Exception as e:
                print(f"Error deleting temporary file {tmp_path}: {e}")



