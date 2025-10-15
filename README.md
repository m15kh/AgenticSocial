# AgenticSocial

AgenticSocial is a Python-based application that leverages CrewAI and LitServe to summarize web content and generate engaging social media posts. It uses a combination of language models and tools to fetch, analyze, and summarize web pages, and then craft concise, shareable messages.

## Features

- **Webpage Summarization**: Extracts key insights from any article or webpage.
- **Social Media Content Creation**: Generates engaging Telegram messages or tweets from the summarized content.
- **Configurable**: Easily modify settings like the language model, API keys, and server configurations via `config.yaml`.

## Prerequisites

- Python 3.8 or higher
- Required Python packages (see `requirements.txt` or install dependencies as described below)
- A valid API key for the Firecrawl tool

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/AgenticSocial.git
   cd AgenticSocial
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the configuration file:
   - Create a `config.yaml` file in the root directory (if it doesn't already exist).
   - Refer to the `load_config` function in `scripts/src/server.py` for the default configuration structure.

4. Ensure the `data/` directory exists:
   ```bash
   mkdir -p data
   ```

## Usage

1. Start the server:
   ```bash
   python scripts/src/server.py
   ```

2. The server will start on the host and port specified in the `config.yaml` file (default: `0.0.0.0:8000`).

3. Make a POST request to the `/predict` endpoint with the following JSON payload:
   ```json
   {
       "url": "https://example.com/some-article"
   }
   ```

4. The server will return a JSON response containing:
   - The summarized content
   - A crafted social media message
   - The file path where the results are saved

## Configuration

The `config.yaml` file allows you to customize the following settings:

- **Language Model**:
  - `model`: The model name (e.g., `qwen2.5`)
  - `provider`: The provider name (e.g., `ollama`)
  - `base_url`: The base URL for the language model API

- **API Keys**:
  - `firecrawl`: Your Firecrawl API key

- **Server**:
  - `host`: The host address for the server
  - `port`: The port number for the server

## Example

To summarize the webpage at `https://aws.amazon.com/what-is/reinforcement-learning-from-human-feedback/`, send the following request:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"url": "https://aws.amazon.com/what-is/reinforcement-learning-from-human-feedback/"}'
```

The response will include the summary, social media message, and the file path where the results are saved.

## File Structure

- `scripts/src/server.py`: Main server script
- `data/`: Directory where results are saved
- `config.yaml`: Configuration file (not included by default; create it manually)

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

## Acknowledgments

- [CrewAI](https://github.com/crewai) for the agent-based framework
- [LitServe](https://github.com/litserve) for the lightweight server framework