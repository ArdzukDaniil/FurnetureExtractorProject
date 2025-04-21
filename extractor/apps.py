from django.apps import AppConfig
from django.conf import settings
import spacy
import logging

logger = logging.getLogger(__name__)


class ExtractorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'extractor'
    nlp_model = None

    def ready(self):
        """
        Этот метод вызывается Django, когда приложение готово.
        Идеальное место для загрузки модели.
        """
        if not self.nlp_model:  # Загружаем только если еще не загружена
            model_path = settings.SPACY_MODEL_PATH
            try:
                logger.info(f"Loading spaCy model from: {model_path}")
                self.nlp_model = spacy.load(model_path)
                logger.info("spaCy model loaded successfully.")
            except OSError as e:
                logger.error(f"Error loading spaCy model from {model_path}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Unexpected error loading spaCy model: {e}", exc_info=True)

        logging.basicConfig(level=logging.INFO)
