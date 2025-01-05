import logging
import time

logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    Responsible for generating content or analysis using a generative language model.
    """

    def __init__(self, genai, api_key, model_name='gemini-1.5-pro', request_interval=40):
        """
        :param genai: A generative AI module or library.
        :param api_key: API key for authentication with the generative model.
        :param model_name: Model name to use for generating content.
        :param request_interval: Seconds to wait between requests to avoid rate limits.
        """
        self.genai = genai
        self.api_key = api_key
        self.model_name = model_name
        self.request_interval = request_interval
        self._configure_model()

    def _configure_model(self):
        """Configure the generative model with the provided API key."""
        if not self.api_key:
            logger.error("API key is required for ContentGenerator.")
            raise ValueError("API key is required.")
        self.genai.configure(api_key=self.api_key)
        self.model = self.genai.GenerativeModel(self.model_name)

    def generate_content(self, prompt):
        """
        Generate content using the language model. Handles potential errors with retries.

        :param prompt: A string prompt for the model.
        :return: The generated text, or None on failure.
        """
        logger.info("Sending prompt to the generative model.")
        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            excpt = str(e)
            if '500' in excpt or '503' in excpt:
                logger.warning(f"Error 500/503 encountered, retrying in 1 minute: {excpt}")
                time.sleep(60)  # Wait for 1 minute before retrying
                try:
                    response = self.model.generate_content(prompt)
                except Exception as retry_e:
                    logger.error(f"Retry failed: {retry_e}")
                    return None
            else:
                logger.error(f"Error generating content: {e}")
                return None

        logger.info("Generated content successfully.")
        # Wait to respect request interval (helps avoid rate limits)
        time.sleep(self.request_interval)

        try:
            return response.text
        except ValueError as ve:
            logger.error(f"ValueError parsing text: {ve}")
            return None