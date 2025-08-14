import os
from dotenv import load_dotenv
import uvicorn
from controller.listener import app as slack_app
from controller.generator import Generator

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_env() -> dict:
    """Load environment variables from setting.env"""
    try:
        env_path = os.path.join(os.path.dirname(__file__), "setting.env")
        if not os.path.exists(env_path):
            raise FileNotFoundError(f"Environment file not found at {env_path}")
        
        load_dotenv(dotenv_path=env_path)
        env_vars = {
            # LLM Settings
            "LLM": os.getenv("LLM"),
            "CHATGPT_API_KEY": os.getenv("CHATGPT_API_KEY"),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
            
            # Elastic Search Settings
            "ELASTIC_HOST": os.getenv("ELASTIC_HOST"),
            "ELASTIC_USER": os.getenv("ELASTIC_USER"),
            "ELASTIC_PASSWORD": os.getenv("ELASTIC_PASSWORD"),
            "ELASTIC_PORT": os.getenv("ELASTIC_PORT"),
            
            # Slack Settings
            "SLACK_API_TOKEN": os.getenv("SLACK_API_TOKEN"),
            "SLACK_SIGNING_SECRET": os.getenv("SLACK_SIGNING_SECRET"),
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN")
        }
        
        # Validate required environment variables
        missing_vars = [key for key, value in env_vars.items() if value is None]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return env_vars
        
    except Exception as e:
        logger.error(f"Error loading environment variables: {str(e)}")
        raise

def run_server():
    """Run the FastAPI server for Slack bot"""
    try:
        logger.info("Starting Slack bot server...")
        uvicorn.run(
            "controller.listener:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            workers=1
        )
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        raise



# question = 'create dt와 관련된 문서'

if __name__ == "__main__":
    try:
        # Load environment variables first to validate configuration
        load_env()
        # Start the server
        run_server()
        # generator = Generator(env)
        # generator.get_answer(question)
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        exit(1)