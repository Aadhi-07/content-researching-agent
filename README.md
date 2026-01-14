# Content Research Agent

An AI-powered research agent that automatically generates research reports and content ideas based on programming and technology topics. The agent integrates with Notion to create structured documents and can be triggered via webhook or API calls.

## 🎯 Use Case

This AI agent is designed for content creators in the programming and technology space. It:

- **Researches** programming topics, frameworks, tools, and technologies
- **Generates** comprehensive research reports with sources
- **Creates** content ideas for various formats (videos, blog posts, social media)
- **Automatically** publishes results to Notion as structured documents
- **Supports** webhook integration for automated workflows

Perfect for:
- Tech content creators looking to streamline research
- Developers wanting to stay updated on new technologies
- Content teams needing automated research workflows
- Anyone building knowledge bases around programming topics

## 🚀 Features

- **Intelligent Research**: Uses web search to gather up-to-date information
- **Content Ideas Generation**: Creates content suggestions for multiple formats
- **Notion Integration**: Automatically creates structured pages in your Notion workspace for the research and content ideas
- **Webhook Support**: Can be triggered by Notion Webhooks (I'll show you how I set this up below)
- **Background Processing**: Returns immediate response while processing continues to avoid timeouts
- **Docker Ready**: Easy deployment with containerization

## 📋 Prerequisites

- Python 3.11+
- Notion API access
- OpenAI API key (for the agents)
- Docker (for containerized deployment)

## ⚙️ Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# API Security
API_KEY=your-secure-api-key-here

# Notion Integration
NOTION_API_KEY=secret_your-notion-integration-token

# OpenAI (if using OpenAI models)
OPENAI_API_KEY=your-openai-api-key

```

### Getting API Keys

1. **Notion API Key**:
   - Go to [Notion Integrations](https://www.notion.so/my-integrations)
   - Create a new integration
   - Copy the "Internal Integration Token"
   - Share your Notion database with the integration

2. **OpenAI API Key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new secret key
   - Copy the key to your `.env` file

3. **API_KEY**:
   - Generate a secure random string for API authentication
   - This protects your endpoint from unauthorized access

## 🔧 Installation

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd content-research-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Run the application:
```bash
uvicorn main:app --reload
```


## 📡 API Usage

### Endpoint: `POST /process`

Triggers the content research process for a given topic.

#### Headers
```
Content-Type: application/json
x-api-key: your-api-key-here
```

#### Request Body (Notion Webhook Format)
```json
{
  "data": {
    "id": "notion-page-id",
    "properties": {
      "Title": {
        "title": [
          {
            "text": {
              "content": "Your Research Topic"
            }
          }
        ]
      }
    }
  }
}
```

#### Response
```json
{
  "status": "processing",
  "message": "Research started for topic: Your Research Topic"
}
```

### Example cURL Request
```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key-here" \
  -d '{
    "data": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "properties": {
        "Title": {
          "title": [
            {
              "text": {
                "content": "React Server Components"
              }
            }
          ]
        }
      }
    }
  }'
```

### Health Check
```bash
curl -H "x-api-key: your-api-key-here" http://localhost:8000/
```

## 📝 Setting up Notion Webhook Trigger

I've created this agent to be triggered manually via a button element in Notion. You can also set up a webhook to trigger the agent when a new item is added to a Notion database.

Inside of my Notion database, I have a page template for every new item that is added. This template contains a button that triggers the agent to run and generate content ideas and a research report based on the topic of the page.

Here's how to setup the button in Notion:

1. Add a new button using "/button" in Notion

![Notion Create Button](docs/create-button.png)

2. Configure the button to run a webhook
   - Set the URL to your agent endpoint (e.g., `https://yourdomain.com/process`)
   - Set the method to POST
   - Set the headers to include your API key:
     ```
     x-api-key: your-api-key-here
     ```
    - Select the "Title" property from the Notion database to be sent as the request body.
![Notion Webhook Config](docs/webhook-config.png)



## 🔗 Notion Integration

### Setting up Notion Webhook

1. Create a Notion database with a "Title" property
2. Set up a Notion automation that triggers on new items
3. Configure the automation to send a POST request to your agent endpoint
4. Use the webhook payload format shown in the API documentation

### Generated Content

The agent creates two types of Notion pages:

1. **Research Report**: Comprehensive analysis of the topic with sources
2. **Content Ideas**: Creative suggestions for various content formats

## 🛠️ Development

### Project Structure
```
content-research-agent/
├── main.py              # FastAPI application and agents
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Development compose file
├── .env                # Environment variables
└── README.md           # This file
```

### Adding New Features

1. **New Agent Types**: Extend the `Agent` classes in `main.py`
2. **Custom Blocks**: Modify `NotionBlock` model for new Notion block types
3. **Additional Endpoints**: Add new FastAPI routes for different workflows

## 🔒 Security

- API key authentication on all endpoints
- Environment-based configuration
- No sensitive data in logs
- Docker security best practices

## 📝 Logging

The application logs important events:
- Request processing status
- Notion API responses
- Agent execution results
- Error details

Monitor logs with:
```bash
docker logs content-research-agent -f
```

## 🐛 Troubleshooting

### Common Issues

1. **422 Validation Errors**: Check request body format matches expected schema
2. **403 Forbidden**: Verify API key is correct and included in headers
3. **Notion API Errors**: Ensure integration has proper permissions
4. **Timeout Issues**: Background processing prevents webhook timeouts

### Debug Mode

Run with debug logging:
```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```
