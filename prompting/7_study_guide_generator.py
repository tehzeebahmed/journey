"""
LangChain Project no 7: Study Guide Generator
Using this as a starting point for the Study Guide Generator project

Here in this project, we will create a Study Guide Generator that 
takes a topic or subject as input and produces a comprehensive study guide. 
The guide will include key concepts, important dates, definitions, 
and practice questions. This tool will be useful for students 
preparing for exams or anyone looking to learn about a new topic 
in a structured way.
"""

import os
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableMap

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# CONSTANTS
# ============================================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
TEMPERATURE = 0.7

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.
    
    Returns:
        bool: True if all variables are set, False otherwise
        
    Raises:
        RuntimeError: If required variables are missing
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY not found in environment.\n"
            "Please set: export GOOGLE_API_KEY='your_key' or add to .env file"
        )
    
    logger.info("Environment variables validated")
    return True


def initialize_llm() -> ChatGoogleGenerativeAI:
    # this function initializes the Gemini LLM with the specified 
    # model and temperature settings.
    # initialize_llm() -> ChatGoogleGenerativeAI means that the function is 
    # expected to return an instance of ChatGoogleGenerativeAI.
    # and the way it is written is wrapped in a try-except block to catch 
    # any exceptions that may occur during initialization,
    # logging an error message if initialization fails, and re-raising the 
    # exception to ensure that
    """
    Initialize and return the Google Gemini LLM.
    
    Returns:
        ChatGoogleGenerativeAI: Configured LLM instance
        
    Raises:
        RuntimeError: If LLM initialization fails
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            timeout=60
        )
        logger.info(f"\n LLM initialized: {MODEL_NAME}")
        return llm
    except Exception as e:
        logger.error(f"\n\n ** Failed to initialize LLM: {e}")
        raise


def validate_input(text: str, min_length: int = 1, max_length: Optional[int] = None) -> bool:
    """
    Validate input text.
    
    Args:
        text: Text to validate
        min_length: Minimum required length
        max_length: Maximum allowed length (None = no limit)
        
    Returns:
        bool: True if valid
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(text, str):
        raise ValueError(f"\n** Input must be string, got {type(text)}")
    
    if len(text) < min_length:
        raise ValueError(f"\n** Input too short (min {min_length} chars)")
    
    if max_length and len(text) > max_length:
        raise ValueError(f"\n** Input too long (max {max_length} chars)")
    
    return True


# ============================================================================
# MAIN PROJECT CLASS
# ============================================================================

class StudyGuideGenerator:
    # what this class does is it encapsulates all the functionality of the 
    # study guide generator project.
    # It initializes the LLM, sets up prompt templates, and defines 
    # methods for processing input
    """
    A study guide generator that creates comprehensive study guides based on a given topic.
    
    This project demonstrates:
    - [Concept 1: e.g., PromptTemplate usage]
    - [Concept 2: e.g., Multiple tones/styles]
    - [Concept 3: e.g., Sequential chains]
    
    Attributes:
        llm: Initialized ChatGoogleGenerativeAI instance
        
    Example:
        >>> project = StudyGuideGenerator(tone="formal")
        >>> result = project.process("input text")
        >>> print(result)
    """
    
    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None, **kwargs):
        """
        Initialize the project.
        
        Args:
            llm: Optional LLM instance. If None, initializes default
            **kwargs: Additional configuration parameters
        """
        self.llm = llm or initialize_llm()
        
        # Store configuration
        # why we need self.config = kwargs is to allow for flexible configuration 
        # of the project.
        self.config = kwargs
        # and the vaklues for kwargs can be passed when creating an instance of the 
        # StudyGuideGenerator,
        # for example, you could create an instance with a specific tone like this:
        # project = StudyGuideGenerator(tone="formal")
        # and then the config dictionary would contain {"tone": "formal"}, 
        # which can be accessed
        
        # Initialize prompt templates
        self._setup_prompts()
        
        logger.info(f"{self.__class__.__name__} initialized")
        #what values will be logged here is the name of the class, 
        # which is "StudyGuideGenerator", 
        # and a message indicating that the initialization was successful.
    
    def _setup_prompts(self) -> None:
        """
        Set up all prompt templates.
        
        This method creates all the PromptTemplate and ChatPromptTemplate
        instances needed for the project.
        """
        # EXAMPLE: For a project with multiple tones
        self.prompt_formal = PromptTemplate.from_template(
            "You are a professional assistant.\n"
            "Process the following: {input_text}\n"
            "Respond in formal tone."
        )
        
        self.prompt_casual = PromptTemplate.from_template(
            "You are a friendly assistant.\n"
            "Process the following: {input_text}\n"
            "Respond in casual, friendly tone."
        )
        
        # EXAMPLE: For a project with ChatPromptTemplate
        self.chat_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("human", "{user_input}"),
        ])
        #difference between PromptTemplate and ChatPromptTemplate is that 
        # the latter is designed for multi-turn conversations, 
        # allowing you to define a sequence of messages with different roles 
        # (system, human, assistant), while PromptTemplate is a simpler template 
        # for single-turn interactions.
    
    def _create_chain(self, prompt_template) -> object:
        """
        Create an LCEL chain from a prompt template.
        
        Args:
            prompt_template: PromptTemplate or ChatPromptTemplate instance
            
        Returns:
            LCEL chain (Runnable)
        """
        chain = (
            prompt_template
            | self.llm
            | StrOutputParser()
        )
        return chain
    
    def process(self, input_text: str) -> str:
        """
        Process the input and return the result.
        
        Args:
            input_text: Text to process
            
        Returns:
            str: Processed result
            
        Raises:
            ValueError: If input validation fails
            Exception: If processing fails
        """
        try:
            # Validate input
            validate_input(input_text, min_length=1)
            
            logger.info(f"Processing input ({len(input_text)} chars)...")
            
            # Choose prompt based on configuration
            tone = self.config.get("tone", "formal")
            
            if tone == "formal":
                chain = self._create_chain(self.prompt_formal)
            elif tone == "casual":
                chain = self._create_chain(self.prompt_casual)
            else:
                raise ValueError(f"Unknown tone: {tone}")
            
            # Invoke the chain
            result = chain.invoke({"input_text": input_text})
            
            logger.info(f"{self.__class__.__name__} completed processing")
            return result
            
        except ValueError as e:
            logger.error(f"\n\n**Input validation failed: {e}**")
            raise
        except Exception as e:
            logger.error(f"\n\n**Processing failed: {e}**")
            raise
    
    def process_batch(self, texts: List[str]) -> List[str]:
        #difference between process and process_batch is that 
        # the latter is designed to handle a list of input texts, 
        # processing each one in turn and returning a list of results. 
        # This allows for efficient batch processing of multiple inputs, 
        # while the process method is focused on handling a single input 
        # at a time.
        """
        Process multiple texts.
        
        Args:
            texts: List of texts to process
            
        Returns:
            List of processed results
        """
        results = []
        for i, text in enumerate(texts, 1):
            try:
                logger.info(f"Processing item {i}/{len(texts)}...")
                result = self.process(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process item {i}: {e}")
                results.append(None)
        
        return results


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

def main():
    """
    Main entry point demonstrating project usage.
    """
    print("\n" + "="*70)
    print("[StudyGuideGenerator]".center(70))
    print("="*70 + "\n")
    
    try:
        # Validate environment
        validate_environment()
        
        # Initialize project
        logger.info("Initializing project...")
        
        project = StudyGuideGenerator(tone="formal")
        
        # EXAMPLE 1: Single input
        print("\n\n***EXAMPLE 1: Single Input Processing")
        print("-" * 70)
        
        input_text = input("Enter a topic or subject for the study guide: ")
        tone = input("Enter desired tone (formal/casual): ")
        print(f"Input: {input_text}\n")
        
        result = project.process(input_text)
        print(f"Output:\n{result}\n")
        
        # EXAMPLE 2: Different tone
        print("\n\n***EXAMPLE 2: Casual Tone")
        print("-" * 70)
        
        project_casual = StudyGuideGenerator(tone=tone)
        result_casual = project_casual.process(input_text)
        print(f"Output:\n{result_casual}\n")
        
        # EXAMPLE 3: Batch processing
        print("\n\n***EXAMPLE 3: Batch Processing")
        print("-" * 70)
        
        texts = [
            input("Enter first sample text: "),
            input("\nEnter second sample text: "),
            input("\nEnter third sample text: "),
        ]
        
        results = project.process_batch(texts)
        for i, (text, result) in enumerate(zip(texts, results), 1):
            #ewhat enumerate does is it allows you to loop over the texts and results 
            # simultaneously,
            # while also keeping track of the index (i) for logging purposes. a
            # nd zip is used to pair each input text with its corresponding result,
            print(f"\nItem {i}:")
            print(f"Input: {text}")
            print(f"Output: {result[:1000]}..." if result and len(result) > 1000 else result)
            #we are printing output here with a condition that if the result is not None and its length is greater than 1000 characters,
            # we will print only the first 1000 characters followed by "..." 
            # to indicate that the
            # result is truncated.
        
        print("\n" + "="*70)
        logger.info("✓ All examples completed successfully")
        print("="*70 + "\n")
        
    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    
    return 0


# ============================================================================
# TESTING
# ============================================================================

def test_project():
    """
    Run tests for the project.
    
    This is a basic test function. Expand with more test cases.
    """
    print("\nRunning tests...")
    # how this test can be called is by running the script with a "test" argument, 
    # for example:
    # python 7_study_guide_generator.py test
    try:
        validate_environment()
        project = StudyGuideGenerator()
        
        # Test 1: Basic functionality
        print("Test 1: Initialization - PASSED")
        
        # Test 2: Single processing
        result = project.process("test input")
        assert isinstance(result, str), "Result should be string"
        assert len(result) > 0, "Result should not be empty"
        print("Test 2: Single processing - PASSED")
        
        # Test 3: Batch processing
        results = project.process_batch(["test1", "test2"])
        assert len(results) == 2, "Should return 2 results"
        print("Test 3: Batch processing - PASSED")
        
        print("\n All tests passed!\n")
        
    except AssertionError as e:
        print(f"\n\nTest failed: {e}\n")
        return False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}\n")
        return False
    
    return True


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        success = test_project()
        sys.exit(0 if success else 1)
    else:
        # Run main
        exit_code = main()
        sys.exit(exit_code)
