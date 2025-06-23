from langchain_experimental.utilities import PythonREPL
from langchain.tools import Tool
from langchain_community.tools import TavilySearchResults
from langchain_community.document_loaders import WikipediaLoader

import re

# For newer LangChain versions, sometimes it's directly from langchain.tools.python
# from langchain.tools.python.tool import PythonREPLTool

python_repl = PythonREPL()

# Create the Tool object to pass to the agent
# Make sure to update the name if you change it from 'python_repl'
repl_tool = Tool(
    name="python_repl",
    description="""
    A Python REPL (Read-Eval-Print Loop) for executing Python code.
    Use this tool for:
    - Performing accurate calculations (arithmetic, complex math).
    - Manipulating and analyzing data (e.g., lists, numbers).
    - Executing small, self-contained Python scripts.

    **Input Format (CRITICAL):**
    The input MUST be a valid, executable Python code string.
    If you want to see the result of an expression or variable, you MUST explicitly `print()` it.
    Example: `print(2 + 2)`
    Example:
    ```python
    x = 10
    y = 20
    print(x * y)
    ```

    **DO NOT:**
    - Ask questions in natural language.
    - Expect implicit output (always use `print()`).
    - Attempt to run interactive commands or scripts that require user input.
    - Write code that requires external files or non-standard libraries unless explicitly provided or permitted.
    - Access the internet or external resources unless the environment allows it.

    **Output:**
    The tool returns the standard output (stdout) of the executed Python code.
    If there is an error in the code, the error message will be returned instead.
    """,
    func=python_repl.run,
)


from langchain_community.tools import TavilySearchResults
from langchain.tools import Tool
from typing import List, Optional
from langchain_community.tools import TavilySearchResults
from langchain.tools import Tool
from typing import List, Optional

def get_travily_api_search_tool(
    tavily_api_key: str,
    # Optional parameters for more fine-grained control
    search_depth: str = "advanced",
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    time_range: Optional[str] = None
) -> Tool:
    """
    Creates and returns a LangChain Tool for Tavily Search API, optimized for GAIA-like
    fact-based questions to improve consistency and accuracy.

    Args:
        tavily_api_key: The API key for Tavily Search.
        search_depth: 'basic' or 'advanced'. 'advanced' can provide more comprehensive results.
                      Default: 'advanced' for better factual depth.
        include_domains: Optional list of domains to specifically include in search results.
                         Useful for targeting highly reputable sources.
        exclude_domains: Optional list of domains to specifically exclude from search results.
                         Useful for filtering out unreliable sources.
        time_range: Optional time range for results (e.g., 'day', 'week', 'month', 'year').
                    Useful for stabilizing results for historical facts or focusing on recent data.

    Returns:
        A LangChain Tool configured for Tavily Search.
    """

    # Prepare parameters for TavilySearchResults
    # Ensure include_domains and exclude_domains are lists, even if empty
    # This resolves the Pydantic ValidationError
    _include_domains = include_domains if include_domains is not None else []
    _exclude_domains = exclude_domains if exclude_domains is not None else []


    tavily_search = TavilySearchResults(
        max_results=5,
        include_answer=False,
        include_raw_content=False,
        include_images=False,
        tavily_api_key=tavily_api_key,
        search_depth=search_depth,
        include_domains=_include_domains,  # Pass the validated list
        exclude_domains=_exclude_domains,  # Pass the validated list
        time_range=time_range
    )

    return Tool(
        name="tavily_search",
        description="""
        A powerful and precise search engine tool for real-time, factual information retrieval from the web.
        Optimized for fact-based questions (like GAIA Level 1 & 2).

        Use this tool when you need to:
        - Find definitive, up-to-date facts, statistics, or direct answers.
        - Research specific historical events, scientific data, or definitions.
        - Answer questions that require external knowledge not present in the model's training data.
        - Verify information or get unambiguous factual answers.

        **Input Format (CRITICAL):**
        The input MUST be a concise, clear, and highly specific search query string.
        Formulate your query as if you're trying to get a single, factual answer from a search engine.
        Example: "population of Tokyo 2023"
        Example: "date of birth of Marie Curie"
        Example: "chemical formula of water"
        Example: "winner of 2022 FIFA World Cup"

        **DO NOT:**
        - Ask natural language questions that are not optimized for search queries (e.g., "Tell me a story about...").
        - Provide incomplete sentences, ambiguous terms, or conversational filler.
        - Include personal information or sensitive data.
        - Expect direct execution of commands or calculations; this is solely a search and information retrieval tool.

        **Output:**
        The tool returns a JSON string containing relevant search results, primarily focused on providing
        snippets and URLs to help you extract the precise factual answer.
        It does NOT provide a direct generated answer but raw search results for your interpretation.
        """,
        func=tavily_search.run,
    )
import requests
from langchain.tools import Tool
import os

def download_and_save_file(args: dict) -> str:
    """
    Downloads a file from a given URL and saves it to a specified local filename.
    Useful for downloading binary files like spreadsheets, images, or archives that
    need to be processed by other tools locally (e.g., python_repl).

    **Input:** A JSON string with 'url' and 'local_filename' keys.
    Example: {"url": "https://example.com/data.xlsx", "local_filename": "data.xlsx"}

    **Output:** Returns a success message with the local filename, or an error message.
    """
    try:
        # Ensure the input is parsed if it comes as a string (common from LLMs)
        if isinstance(args, str):
            import json
            args = json.loads(args)

        url = args.get("url")
        local_filename = args.get("local_filename")

        if not url or not local_filename:
            return "Error: Both 'url' and 'local_filename' must be provided."

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Ensure the directory exists if local_filename includes a path
        os.makedirs(os.path.dirname(local_filename) or '.', exist_ok=True)

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return f"File downloaded successfully to {local_filename}"

    except requests.exceptions.RequestException as e:
        return f"Error downloading file from {url}: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Add this tool to your list of tools
file_saver_tool = Tool(
    name="file_saver",
    description="""
    Downloads a file from a URL and saves it to a specified local filename.
    Input must be a JSON string with 'url' and 'local_filename' keys.
    Use this for downloading binary files like Excel sheets (.xlsx), images, or PDFs.
    Example: '{"url": "https://example.com/data.xlsx", "local_filename": "my_data.xlsx"}'
    """,
    func=download_and_save_file,
)

import speech_recognition as sr
import os
import requests # Still needed for file_saver, but its logic removed from this function
from pydub import AudioSegment # You'll need pydub and ffmpeg/libav for this to work

def transcribe_audio_from_path(local_audio_path: str, language: str = "en-US") -> str:
    """
    Transcribes audio content from a local file path to a text string.

    This tool is designed to convert spoken content from a locally saved audio file
    into written text. It expects a path to an audio file that has already been
    downloaded and saved to the local environment (e.g., using 'file_saver').
    Supports various audio formats (e.g., MP3, WAV) and converts them to WAV internally for transcription.
    For best results, specify the correct language code (e.g., 'en-US' for US English, 'es-ES' for Spanish).

    Args:
        local_audio_path (str): The local file path to the audio (e.g., "my_recording.mp3").
                                This MUST be a path to a file already existing on disk.
        language (str, optional): The spoken language in the audio. Defaults to "en-US".
                                 Refer to Google Speech Recognition language codes for options.

    Returns:
        str: The transcribed text, or an informative error message if transcription fails.
    """
    r = sr.Recognizer()
    temp_wav_path = "temp_audio_to_transcribe.wav" # Temporary WAV file for transcription
    transcribed_text = ""

    try:
        # Ensure it's a local path and file exists
        if local_audio_path.startswith("http://") or local_audio_path.startswith("https://"):
            return "Error: This tool only accepts local file paths, not URLs. Please use 'file_saver' first."

        if not os.path.exists(local_audio_path):
            return f"Error: Local audio file not found at '{local_audio_path}'."

        # Convert to WAV if not already (SpeechRecognition prefers WAV)
        audio = AudioSegment.from_file(local_audio_path)
        audio.export(temp_wav_path, format="wav")

        # Transcribe the audio
        with sr.AudioFile(temp_wav_path) as source:
            audio_listened = r.record(source)
            try:
                transcribed_text = r.recognize_google(audio_listened, language=language)
            except sr.UnknownValueError:
                return "Could not understand audio (speech not clear or too short)."
            except sr.RequestError as e:
                return f"Could not request results from Google Speech Recognition service; {e}"

    except FileNotFoundError: # This should be caught by os.path.exists now, but good for robustness
        return f"Error: Audio file not found at '{local_audio_path}'."
    except Exception as e:
        return f"An unexpected error occurred during audio processing or transcription: {e}"
    finally:
        # Clean up temporary WAV file
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

    return transcribed_text.strip()

# Get your audio_transcriber tool
from langchain.tools import Tool

audio_transcriber_tool = Tool(
    name="audio_transcriber_tool",
    description=(
        "Transcribes audio content from a **local file path** to a text transcript. "
        "This tool is useful for extracting spoken information from audio recordings "
        "that have been previously downloaded and saved to the local environment "
        "(e.g., using the 'file_saver' tool). "
        "Input MUST be a local file path (e.g., 'path/to/audio.mp3'). "
        "Do NOT pass URLs directly to this tool. "
        "Optionally, provide the 'language' parameter (e.g., 'en-US', 'es-ES') for better accuracy. "
        "Returns the transcribed text or an informative error message if transcription fails."
    ),
    func=transcribe_audio_from_path, 
)

from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import Tool # Ensure Tool is imported


import os
from serpapi import GoogleSearch # Or use SerpApiClient for other engines
from typing import Dict, Any
from langchain.tools import Tool # Import the Tool class

class SerpApiSearchTool:
    """
    A tool to perform searches using SerpApi.
    Supports various search engines and extracts structured data.
    """
    def __init__(self):
        # Retrieve API key from environment variables for security
        self.api_key = os.getenv("SERPAPI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "SERPAPI_API_KEY must be set as an environment variable. "
                "Get your API key from https://serpapi.com/dashboard"
            )

    def search_google(self, query: str, num_results: int = 5) -> str:
        """
        Performs a Google search via SerpApi and returns a formatted string of organic results.

        Args:
            query (str): The search query string.
            num_results (int): The number of organic search results to return (max 100).

        Returns:
            str: A formatted string containing the title, link, and snippet of each result.
                 Also includes any featured snippet or knowledge graph if available.
                 Returns an error message if the search fails or no results are found.
        """
        if not query:
            return "Error: Search query cannot be empty."

        params = {
            "api_key": self.api_key,
            "engine": "google",
            "q": query,
            "num": num_results, # Number of organic results
            "gl": "in",         # Geo-location for the search (India in this case)
            "hl": "en"          # Host language for the search
        }

        try:
            print(f"[TOOL: SerpApiSearch] Searching Google for: '{query}'")
            search = GoogleSearch(params)
            results = search.get_dict() # Execute the search and get results as a dictionary

            formatted_output = []

            # Check for common structured results first
            if 'answer_box' in results and results['answer_box'].get('answer'):
                formatted_output.append(f"Answer Box: {results['answer_box']['answer']}")
            if 'knowledge_graph' in results and results['knowledge_graph'].get('description'):
                formatted_output.append(f"Knowledge Graph: {results['knowledge_graph']['description']}")
                if results['knowledge_graph'].get('title'):
                     formatted_output.append(f"  Title: {results['knowledge_graph']['title']}")
                if results['knowledge_graph'].get('link'):
                     formatted_output.append(f"  Link: {results['knowledge_graph']['link']}")

            # Then process organic results
            organic_results = results.get('organic_results', [])
            if organic_results:
                if formatted_output: # Add a separator if other sections were added
                    formatted_output.append("\n--- Organic Results ---")
                else:
                    formatted_output.append("Organic Results:")
                for i, item in enumerate(organic_results):
                    title = item.get('title', 'No Title')
                    link = item.get('link', '#')
                    snippet = item.get('snippet', 'No Snippet')
                    formatted_output.append(
                        f"Result {i+1}:\n"
                        f"  Title: {title}\n"
                        f"  Link: {link}\n"
                        f"  Snippet: {snippet}\n"
                    )
            
            if not formatted_output: # If no structured data or organic results
                return "No relevant search results found."

            return "\n".join(formatted_output)

        except Exception as e:
            return f"Error performing SerpApi search: {e}"

# Instantiate the SerpApiSearchTool class
serpapi_search_instance = SerpApiSearchTool()

# Create the LangChain Tool object
serpapi_Google_Search_tool = Tool(
    name="serpapi_Google Search",
    description="""
    Performs a Google search using SerpApi to get current and detailed information from the web.
    Use this for factual queries, general knowledge, recent events, or when TavilySearch might not be sufficient.
    It can return rich results including answer boxes, knowledge graphs, and multiple organic search results.
    Input should be a clear, concise search query string.
    """,
    func=serpapi_search_instance.search_google,
)

# Remember to set your SERPAPI_API_KEY environment variable before running!
# Example: os.environ["SERPAPI_API_KEY"] = "YOUR_API_KEY_HERE"

# To use this tool, you would add `serpapi_Google Search_tool` to your `tools` list
# in your `BasicAgent` initialization, like this:
# tools = [travily_api_search_tool, python_repl, ..., serpapi_Google Search_tool]
#
# And you would need to update your prompt's "Available Tools" section
# to describe `serpapi_Google Search` to the LLM.

# In helper.py

import base64
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os

# Your existing tools (PythonREPL, TavilySearchResults, file_saver, audio_transcriber, Wikipedia, SerpAPI) go here...
# ... (rest of your helper.py code for other tools) ...

import base64
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os

def analyze_image_with_gemini(args: dict) -> str:
    """
    Analyzes an image using Google's Gemini Multimodal LLM to answer a given question.
    This tool is designed for tasks requiring visual understanding, such as
    describing image content, identifying objects, or answering questions about
    information presented visually (e.g., charts, diagrams, chess boards).

    **Input Format (CRITICAL):**
    The input MUST be a JSON string with 'image_path' and 'question' keys.
    - 'image_path': The local file path to the image (e.g., 'path/to/my_image.png').
      This image MUST have been previously downloaded and saved locally using the 'file_saver' tool.
    - 'question': The question to answer based on the image content.

    Example: '{"image_path": "downloaded_image.png", "question": "What is depicted in this image?"}'
    Example: '{"image_path": "chess_board.jpg", "question": "What is the next best move in this chess position?"}'

    **DO NOT:**
    - Pass URLs directly to this tool; always use 'file_saver' first.
    - Ask questions unrelated to the image content.
    - Expect real-time actions or external website access.

    **Output:**
    The tool returns the answer generated by the Gemini Multimodal LLM based on the image and question.
    Returns an informative error message if the image file is not found,
    the API key is missing, or the LLM encounters an issue.
    """
    try:
        # Ensure the input is parsed if it comes as a string (common from LLMs)
        if isinstance(args, str):
            import json
            args = json.loads(args)

        image_path = args.get("image_path")
        question = args.get("question")

        if not image_path or not question:
            return "Error: Both 'image_path' and 'question' must be provided."

        if not os.path.exists(image_path):
            return f"Error: Local image file not found at '{image_path}'. Did you save it with 'file_saver'?"

        google_api_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_api_key:
            return "Error: GOOGLE_API_KEY not found in environment variables for multimodal tool."

        # Initialize the multimodal LLM (Gemini-Pro-Vision is recommended for image understanding)
        # Using a fallback to 'gemini-pro' if 'gemini-pro-vision' isn't directly available or preferred
        llm = ChatGoogleGenerativeAI(
            #model="gemini-pro-vision" if "gemini-pro-vision" in ChatGoogleGenerativeAI.get_available_models(google_api_key) else "gemini-2.0-flash",
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.0 # Set temperature to 0 for more factual/deterministic responses
        )

        # Load the image as base64 for multimodal input
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Create a multimodal message for the LLM
        message = HumanMessage(
            content=[
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
            ]
        )

        # Invoke the LLM
        response = llm.invoke([message])
        return response.content

    except Exception as e:
        return f"Error in gemini_multimodal_tool: {e}"

# Define the Tool object for the agent
gemini_multimodal_tool = Tool(
    name="gemini_multimodal_tool",
    description=analyze_image_with_gemini.__doc__, # Use the docstring as description
    func=analyze_image_with_gemini,
)


def wiki_search(query: str) -> str:
    """Search Wikipedia for a query and return maximum 2 results.
    
    Args:
        query: The search query.
    Returns:
        A string with formatted Wikipedia search results.
    """
    search_docs = WikipediaLoader(query=query, load_max_docs=2).load()
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata.get("source", "")}" page="{doc.metadata.get("page", "")}"/>\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ])
    return formatted_search_docs

wikipedia_search_tool2 = Tool(
    name="wikipedia_search_tool2",
    description=wiki_search.__doc__,
    func=wiki_search,
)