from abc import ABC, abstractmethod
from typing import List, Any
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


import os
import pdfplumber
from typing import List, Any

class PDFParser(DocumentParser):
    def parse(self, file_path: str) -> str:
        """
        Извлекает текст из PDF-файла без изменения ориентации.
        
        :param file_path: Путь к PDF-файлу.
        :return: Извлечённый текст из PDF.
        """
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return (text, 'parsed without rotation')

    def parse_with_rotation(self, file_path: str) -> str:
        """
        Извлекает текст из PDF-файла, удаляет таблицы из общего текста и добавляет только перевёрнутые таблицы.
        Предполагается, что таблицы могут быть перевёрнуты, но страница остаётся вертикальной.
        
        :param file_path: Путь к PDF-файлу.
        :return: Извлечённый текст из PDF с только перевёрнутыми таблицами.
        """
        extracted_text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # Извлечение таблиц и их bounding boxes
                tables = page.extract_tables()
                table_bboxes = []
                rotated_tables_text = ""
                
                for table in tables:
                    if self.__is_table_rotated(page, table):
                        rotated_table = self.__rotate_table_data(table)
                        table_text = self.__convert_table_to_text(rotated_table)
                        rotated_tables_text += table_text + "\n"
                        
                        # Получение bounding box таблицы для удаления её из общего текста
                        table_bbox = self.__get_table_bbox(page, table)
                        if table_bbox:
                            table_bboxes.append(table_bbox)
                
                # Извлечение слов на странице
                words = page.extract_words()
                page_text = ""
                for word in words:
                    word_bbox = (float(word['x0']), float(word['top']), float(word['x1']), float(word['bottom']))
                    # Проверка, находится ли слово вне любых таблиц
                    if not any(self.__is_bbox_overlap(word_bbox, table_bbox) for table_bbox in table_bboxes):
                        page_text += word['text'] + " "
                
                # Добавление текста страницы без таблиц
                if page_text.strip():
                    extracted_text += page_text.strip() + "\n"
                
                # Добавление перевёрнутых таблиц
                if rotated_tables_text.strip():
                    extracted_text += rotated_tables_text.strip() + "\n"
        
        return (extracted_text, 'parsed_with_rotation')

    def __is_bbox_overlap(self, bbox1: tuple, bbox2: tuple) -> bool:
        """
        Проверяет, перекрываются ли два bounding box.
        
        :param bbox1: Первой bounding box в виде (x0, top, x1, bottom).
        :param bbox2: Второй bounding box в виде (x0, top, x1, bottom).
        :return: True, если перекрываются, иначе False.
        """
        x0_1, top_1, x1_1, bottom_1 = bbox1
        x0_2, top_2, x1_2, bottom_2 = bbox2
        
        # Проверка на отсутствие перекрытия
        if x1_1 < x0_2 or x0_1 > x1_2:
            return False
        if bottom_1 < top_2 or top_1 > bottom_2:
            return False
        return True
    
    def __get_table_bbox(self, page: pdfplumber.page.Page, table: List[List[Any]]) -> tuple:
        """
        Определяет bounding box таблицы на основе расположения ячеек.
        
        :param page: Объект страницы из pdfplumber.
        :param table: Таблица в виде списка списков.
        :return: Bounding box в виде (x0, top, x1, bottom).
        """
        x0, top, x1, bottom = float('inf'), float('inf'), 0, 0

        for row in table:
            for cell in row:
                if not cell:
                    continue
                # Поиск всех символов, принадлежащих ячейке
                cell_chars = [
                    char for char in page.chars
                    if char['text'].strip() and char['text'].strip() in cell
                ]
                for char in cell_chars:
                    x0 = min(x0, char['x0'])
                    top = min(top, char['top'])
                    x1 = max(x1, char['x1'])
                    bottom = max(bottom, char['bottom'])

        if x0 == float('inf') or top == float('inf'):
            return None

        return (x0, top, x1, bottom)



    def __is_table_rotated(self, page: pdfplumber.page.Page, table: List[List[Any]]) -> bool:
        """
        Определяет, перевёрнута ли таблица на основе ориентации текста в ячейках.
        Предполагается, что перевёрнутые таблицы имеют большинство ячеек с поворотом текста на 90 или 270 градусов.
        
        :param page: Объект страницы из pdfplumber.
        :param table: Таблица в виде списка списков.
        :return: True, если таблица перевёрнута, иначе False.
        """
        if not table:
            return False

        # Получение bounding box таблицы на основе координат ячеек
        table_bbox = self.__get_table_bbox(page, table)
        if not table_bbox:
            return False

        # Извлечение символов внутри bounding box таблицы
        table_chars = [
            char for char in page.chars
            if self.__is_char_in_bbox(char, table_bbox)
        ]

        if not table_chars:
            return False

        # Подсчёт количества символов с поворотом
        rotated_chars = [
            char for char in table_chars
            if not char.get('upright', True)  # 'upright' == False указывает на поворот
        ]

        rotated_ratio = len(rotated_chars) / len(table_chars)

        # Определение перевёрнутости таблицы по порогу (например, более 30% символов перевёрнуты)
        return rotated_ratio > 0.3

    def __get_table_bbox(self, page: pdfplumber.page.Page, table: List[List[Any]]) -> tuple:
        """
        Определяет bounding box таблицы на основе расположения ячеек.
        
        :param page: Объект страницы из pdfplumber.
        :param table: Таблица в виде списка списков.
        :return: Bounding box в виде (x0, top, x1, bottom).
        """
        x0, top, x1, bottom = float('inf'), float('inf'), 0, 0

        for row in table:
            for cell in row:
                if not cell:
                    continue
                # Поиск всех символов, принадлежащих ячейке
                cell_chars = [
                    char for char in page.chars
                    if char['text'].strip() and char['text'].strip() in cell
                ]
                for char in cell_chars:
                    x0 = min(x0, char['x0'])
                    top = min(top, char['top'])
                    x1 = max(x1, char['x1'])
                    bottom = max(bottom, char['bottom'])

        if x0 == float('inf') or top == float('inf'):
            return None

        return (x0, top, x1, bottom)

    def __is_char_in_bbox(self, char: dict, bbox: tuple) -> bool:
        """
        Проверяет, находится ли символ внутри заданного bounding box.
        
        :param char: Словарь с информацией о символе.
        :param bbox: Bounding box в виде (x0, top, x1, bottom).
        :return: True, если символ внутри bbox, иначе False.
        """
        x0, top, x1, bottom = bbox
        return x0 <= char['x0'] <= x1 and top <= char['top'] <= bottom

    def __rotate_table_data(self, table: List[List[Any]]) -> List[List[Any]]:
        """
        Поворачивает таблицу на 90 градусов против часовой стрелки и корректирует ориентацию текста в ячейках.
        
        :param table: Таблица в виде списка списков.
        :return: Повернутая таблица с корректным текстом.
        """
        # Поворот таблицы на 90 градусов против часовой стрелки
        rotated = list(zip(*table))[::-1]
        rotated = [list(row) for row in rotated]
        
        # Коррекция текста в ячейках (разворот текста)
        rotated_corrected = []
        for row in rotated:
            corrected_row = []
            for cell in row:
                if cell:
                    # Разворот строки для корректной ориентации текста
                    corrected_cell = cell[::-1]
                else:
                    corrected_cell = cell
                corrected_row.append(corrected_cell)
            rotated_corrected.append(corrected_row)
        
        return rotated_corrected


    def __convert_table_to_text(self, table: List[List[Any]]) -> str:
        """
        Преобразует таблицу в текстовый формат с использованием табуляции как разделителя.
        
        :param table: Таблица в виде списка списков.
        :return: Таблица в виде текстовой строки.
        """
        table_text = ""
        for row in table:
            # Преобразуем каждую строку таблицы в строку с разделением табуляцией
            row_text = "\t".join([cell if cell else "" for cell in row])
            table_text += row_text + "\n"
        return table_text


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


class DocumentParserFactory:
    @staticmethod
    def parser_file(file_path: str, is_contract: bool):
        if file_path.lower().endswith(".pdf") and "kontrakt" in file_path.lower():
            return PDFParser().parse_with_rotation(file_path)
        elif file_path.lower().endswith(".pdf"):
            return PDFParser().parse(file_path)
        elif file_path.lower().endswith(".docx"):
            return DOCXParser().parse(file_path)
        elif file_path.lower().endswith(".doc"):
            return DOCParser().parse(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {file_path}")
