import asyncio
import json
import logging
from ollama import Client
from typing import Any, List, Dict

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


#инициализируем логгер

logger = logging.getLogger(__name__)

#Инициализируем константы
CHROMA_PATH = './chroma.db'
COLLECTION_NAME = 'my_examples'
EMBED_MODEL = 'nomic-embed-text:v1.5'
OLLAMA_BASE_URL = 'http://localhost:11434/api'


class RAGHandler:
    """класс для работы с векторной БД и поиском примеров"""

    def __init__(self):
        try:
            self.client = chromadb.PersistentClient(
                path=CHROMA_PATH,
                settings=Settings(anonymized_telemetry=False)
            )

            self.embedding_func = embedding_functions.OllamaEmbeddingFunction(
                model_name=EMBED_MODEL,
                url=f'{OLLAMA_BASE_URL}/api/embeddings'
            )
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_func
            )
            #Флаг для проверки загруженны ли все данные
            self._initialized = False
        except Exception as e:
            logger.exception(f'Не удалось инциализировать RAGHandler {e}')
            self._initialized = False
            raise

    async def load_example_from_file(self, file_path: str = 'examples.json'):
        """заружает примеры из JSON  в БД (если коллекция пуста)"""

        try:
            count = self.collection.count()
            if count > 0:
                logger.info(f'Коллекция уже содержит: {count} примеров, пропускаем загрузку')
                self._initialized = True
                return


        #Читаем файл
            with open(file_path, 'r', encoding='utf-8') as f:
                examples = json.load(f)
                logger.info('Содержимое файла: %s', examples)

        except FileNotFoundError:
            logger.error(f'Файл {file_path} не найден. Загрузка отменена')
            return
        except json.JSONDecodeError as e:
            logger.error(f'Ошибка парсинга {file_path} : {e}')
            self._initialized = False
            return

        if not isinstance(examples, list):
            logger.error(f'Файл должен содержать список объектов с полями "question" и "answer"')
            return

        #Подготоваливаем данные для векторной БД
        ids = []
        documents = []
        metadatas = []

        for idx, ex in enumerate(examples):
            question = ex.get('question','').strip()
            answer = ex.get('answer','').strip()
            if not question or not answer:
                logger.warning(f'Пропущен пример {idx} - нет вопроса или ответа')
                continue
            ids.append(str(idx))
            documents.append(question) # Какой вопрос ищем
            metadatas.append({'answer': answer}) # сохраняем ответ в метаданных

        if not ids:
            logger.warning('Нет валидных примеров. Коллекция остается пустой')
            self._initialized = True
            return

        try:
            #добавляем ответ в коллекцию
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f'Загружено {len(ids)} примеров в коллекцию')
        except Exception as e:
            logger.exception(f'Ошибка при добавлении в векторную БД: {e}')
            self._initialized = False
            return
        self._initialized = True


    async def find_relevant_examples(self, query: str, n_results: int = 3) -> List[Dict[str, str]]:
        """Ищет n_results наиболее похожих примеров на запрос query"""
        if not self._initialized:
            logger.warning('Коллекция не инициализированно поиск вернет пустой список')
            return []

        # Выполняем запрос к БД
        # Для безопасности выполним в потоке

        try:
            results = await asyncio.to_thread(
                self.collection.query,
                query_texts=[query],
                n_results=n_results
            )
        except Exception as e:
            logger.error(f"Ошибка при поиске в ChromaDB: {e}")
            return []

        # Извлекаем метаданные
        examples = []
        if results and 'documents' in results and results['documents']:
            # results['documents'] — список списков метаданных для каждого запроса (у нас один запрос)
            docs = results['documents'][0]
            metas = results['metadatas'][0] if results.get('metadatas') else [{}] * len(docs)

            for i in range(len(docs)):
                examples.append({
                    'question': docs[i],
                    'answer': metas[i].get('answer','') if i < len(metas) else ''
                })


rag = RAGHandler()



