import os
import requests
import re
from typing import List, Any, Dict
import urllib.parse
from unidecode import unidecode  # Убедитесь, что библиотека установлена: pip install unidecode
from parser.parser_site_mos import AuctionParser
from parser.parser_documents import DocumentParserFactory, PDFParser

class LLMProcessingEntity:

    def __init__(self, urls_list: List[str], criterions_list: List[int]):
        self.urls = urls_list
        self.criterions = criterions_list
        self.criterions_data = {}
        self.files_data = {}

    def parse(self) -> Dict[str, Any]:
        """
        Parse criterions to condition
        """
        documents_dir = os.path.join(os.getcwd(), "documents")
        
        # Проверка существования 'documents' и обработка конфликтов
        if os.path.exists(documents_dir):
            if os.path.isfile(documents_dir):
                backup_dir = documents_dir + "_backup"
                os.rename(documents_dir, backup_dir)
        else:
            os.makedirs(documents_dir, exist_ok=True)

        for i, url in enumerate(self.urls):
            parser = AuctionParser(url)
            parser.parse_data()
            
            self.criterions_data[i] = {}
            for criterion in self.criterions:
                try:
                    self.criterions_data[i][criterion] = parser.criterion_forms[criterion - 1]
                except IndexError:
                    self.criterions_data[i][criterion] = None
            
            self.files_data[i] = {}
            for j, file in enumerate(parser.files):
                file_id = file.get("id")
                if not file_id:
                    continue  # Пропустить файлы без 'id'
                
                download_url = f"https://zakupki.mos.ru/newapi/api/FileStorage/Download?id={file_id}"
                
                try:
                    response = requests.get(download_url, timeout=10)
                    response.raise_for_status()
                except requests.RequestException:
                    continue  # Пропустить файл при ошибке скачивания
                
                # Извлечение имени файла
                filename = self.__get_filename_from_response(response, file)
                print(filename)
                # Транслитерация имени файла
                
                # Безопасное имя файла
                filename = os.path.basename(filename)
                file_path = os.path.join(documents_dir, filename)
                
                # Проверка на существование файла и предотвращение перезаписи
                if os.path.exists(file_path):
                    filename = self.__generate_unique_filename(documents_dir, filename)
                    file_path = os.path.join(documents_dir, filename)
                
                # Сохранение файла
                if not self.__save_file(file_path, response):
                    continue  # Пропустить файл при ошибке сохранения
                
                # Парсинг содержимого файла
                
                file_text = DocumentParserFactory().parser_file(file_path, is_contract=self.__is_contract_file(file_path))
                self.files_data[i][j] = file_text
                
                # Удаление временного файла после парсинга
                os.remove(file_path)
        
        return {"infoCriterion": self.criterions_data, "filesContent": self.files_data}

    def __is_contract_file(self, filename: str) -> bool:
        """
        Проверяет, содержит ли имя файла слово 'kontrakt'.
        """
        return "kontrakt" in filename.lower()

    def __get_filename_from_response(self, response: requests.Response, file: Dict[str, Any]) -> str:
        """
        Извлекает имя файла из заголовков ответа или из объекта 'file'.
        Поддерживает 'filename*' по RFC 5987 для сохранения кириллических символов.
        """
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            # Используем регулярное выражение для извлечения filename* и filename
            filename_star_match = re.search(r"filename\*\s*=\s*([^;]+)", content_disposition, re.IGNORECASE)
            if filename_star_match:
                filename_encoded = filename_star_match.group(1)
                # Пример: UTF-8''%D0%BA%D0%BE%D0%BD%D1%82%D1%80%D0%B0%D0%BA%D1%82.pdf
                try:
                    # Разделяем на charset, language, and value
                    charset, lang, encoded_filename = filename_encoded.split("'", 2)
                    filename = urllib.parse.unquote(encoded_filename, encoding=charset, errors='replace')
                    # Транслитерация
                    filename = unidecode(filename)
                    return filename
                except ValueError:
                    pass  # Некорректный формат, переходим к следующей попытке
            
            filename_match = re.search(r"filename\s*=\s*\"?([^\";]+)\"?", content_disposition, re.IGNORECASE)
            if filename_match:
                filename = filename_match.group(1)
                # Транслитерация
                filename = unidecode(filename)
                return filename
        
        # Если 'filename*' и 'filename' не найдены или не удалось декодировать, используем 'file.get('name')'
        filename = file.get('name')
        if filename:
            # Транслитерация
            filename = unidecode(filename)
        else:
            # В крайнем случае, используем индекс с расширением по умолчанию
            filename = f"file_{file.get('id', 'unknown')}.bin"
        
        return filename

    def __generate_unique_filename(self, directory: str, filename: str) -> str:
        """
        Генерирует уникальное имя файла, добавляя суффикс, если файл уже существует.
        """
        base, ext = os.path.splitext(filename)
        count = 1
        new_filename = f"{base}_{count}{ext}"
        while os.path.exists(os.path.join(directory, new_filename)):
            count += 1
            new_filename = f"{base}_{count}{ext}"
        return new_filename

    def __save_file(self, file_path: str, response: requests.Response) -> bool:
        """
        Сохраняет файл на диск. Возвращает True при успехе, False при ошибке.
        """
        try:
            with open(file_path, "wb") as f:
                f.write(response.content)
            return True
        except OSError:
            return False

    def display_data(self):
        print(self.files_data)

to_send = LLMProcessingEntity(["https://zakupki.mos.ru/auction/9869562",], [1, 2, 3, 4, 5, 6])
to_send.parse()
to_send.display_data()