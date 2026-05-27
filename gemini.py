import os
import logging
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv() 


logger = logging.getLogger(__name__)


def _check_gemini_api_key():
    if 'GEMINI_API_KEY' not in os.environ:
        logger.error("GEMINI_API_KEY not found in environment variables")
        raise RuntimeError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")


async def get_prompt(path: str) -> str:
    try:
        import aiofiles
        async with aiofiles.open(path, 'r', encoding='utf-8') as file:
            return await file.read()
    except ImportError:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {path}")
            raise FileNotFoundError(f"Error: The file at {path} was not found.")
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {path}")
        raise FileNotFoundError(f"Error: The file at {path} was not found.")


class GeminiModel:
    def __init__(self, prompt_path: str, model: str = 'gemini-flash-lite-latest'):
        _check_gemini_api_key()
        self.client = genai.Client()
        self.prompt_path = prompt_path
        self.model = model
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.config = None
        self.chat = None
        logger.debug(f"GeminiModel initialized with prompt: {prompt_path}, model: {model}")

    async def initialize(self, thinking_budget: int):
        logger.debug(f"Initializing Gemini model with prompt: {self.prompt_path}")
        prompt = await get_prompt(self.prompt_path)

        self.config = types.GenerateContentConfig(
            tools=[self.grounding_tool],
            system_instruction=prompt,
            thinking_config=types.ThinkingConfig(
                thinking_budget=thinking_budget
            )
        )

        self.chat = self.client.aio.chats.create(
            model=self.model,
            config=self.config
        )
        logger.info("Gemini chat session initialized successfully")

    async def generate_response(self, message: str, config: types.GenerateContentConfigDict = None, thinking_budget: int = -1) -> str:
        if self.chat is None:
            logger.debug("Chat session not initialized, initializing now")
            await self.initialize(thinking_budget=thinking_budget)

        logger.debug(f"Generating response from Gemini (message length: {len(message)})")
        if config:
            response = await self.chat.send_message(message=message, config=config)
        else:
            response = await self.chat.send_message(message=message)

        logger.debug(f"Received response from Gemini (length: {len(response.text)})")
        return response.text

    async def generate_response_stream(self, message: str, thinking_budget: int = -1):
        if self.chat is None:
            logger.debug("Chat session not initialized, initializing now")
            await self.initialize(thinking_budget=thinking_budget)

        logger.debug("Starting streaming response from Gemini")
        response_stream = await self.chat.send_message_stream(message=message)
        async for chunk in response_stream:
            yield chunk.text
