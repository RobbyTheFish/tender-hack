from abc import ABC, abstractmethod
import pdfplumber
import docx
import subprocess
import os


class DocumentParserMeta(type(ABC), type):
    pass


class DocumentParser(ABC, metaclass=DocumentParserMeta):
    @abstractmethod
    def parse(self, file_path):
        pass


class PDFParser(DocumentParser):
    def parse(self, file_path):
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text()
        return text


class DOCXParser(DocumentParser):
    def parse(self, file_path):
        text = ""
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text


class DOCParser(DocumentParser):
    def parse(self, file_path):
        # Проверяем, установлена ли утилита antiword
        if not os.system("which antiword > /dev/null 2>&1") == 0:
            raise EnvironmentError(
                "Утилита 'antiword' не установлена. Установите её для парсинга DOC-файлов."
            )

        # Используем antiword для извлечения текста из DOC
        result = subprocess.run(
            ["antiword", file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode != 0:
            raise RuntimeError(f"Ошибка при обработке файла: {result.stderr.decode()}")

        return result.stdout.decode()


class DocumentsParser:
    @staticmethod
    def parser_file(file_path: str):
        if file_path.lower().endswith(".pdf"):
            return PDFParser().parse(file_path)
        elif file_path.lower().endswith(".docx"):
            return DOCXParser().parse(file_path)
        elif file_path.lower().endswith(".doc"):
            return DOCParser().parse(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_path}")
