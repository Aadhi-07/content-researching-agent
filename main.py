from typing import Optional, Union
from agents import Agent, Runner, WebSearchTool, AgentOutputSchema
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
import os
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import requests
from typing import Literal
import json

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

NOTION_API_KEY = os.getenv("NOTION_API_KEY")

# Research Agent

research_agent = Agent(
  name="Research Agent",
  tools=[
    WebSearchTool()
  ],
  instructions=f""""
   <background>
    You are a content researcher for Tom Shaw, a Programming and Tech content creator. It’s your job to research a given topic, write down a summary of each relevant finding and produce a report on what you have found. You always research thoroughly and provide accurate information.
    Your research should focus on the technical aspects of the topic, including programming languages, frameworks, tools, and technologies relevant to the topic. You should also consider the latest trends and best practices in the industry.
    </background>
    <task>
    You should research how the programming and technology behind the topic provided by user works. Once you have researched the topic, write a short report on your findings. You should avoid using too much technical jargon where it is not needed in your report. You should use your web search tool to get accurate up to date information. Your response should include links to the sources you used in your research.
    </task>
    <output>
    A short report (around 500 words) describing your research findings while researching the topic. This report should include a summary of the topic, key concepts, and any relevant sources you found during your research. The report should be beginner-friendly and easy to understand. The report shoulld be formatted markdown so that it can be pasted into a Notion document.
    </output>
  """,
  model="gpt-4.1",
)

# Content Ideas Agent

content_ideas_agent = Agent(
  name="Content Ideas Agent",
  instructions=f""""
    <background>
    You are a content ideas generator for Tom Shaw, a Programming and Tech content creator. It’s your job to generate content ideas based on the topic provided by the user and the research provided to you by the Research Agent. Tom produces content in various formats, including short-form videos, long-form videos, a newsletter, as well as tweets, linkedIn posts and Instagram carousel posts. Your ideas should be diverse and be appealing to the target audience of Tom's content, which includes beginners and enthusiasts in the field of programming and technology.
    Tom's mission is to inspire more people to get into tech by showcasing awesome projects, useful tools and other insights into the world of programming and technology. Your content ideas should align with this mission and be suitable for various formats such as blog posts, videos, or social media posts. You can suggest humourous content, tutorials, guides, project builds, discussions, or any other type of content that would be engaging and informative for the audience.
    </background>
    <task>
    Generate a list of content ideas related to the topic provided by the user. The ideas should be diverse and cover different aspects of Tom's content creation. Each idea should include a brief descriptiption of the content, as well as the format it would be suitable for (e.g., video, blog post, social media post) and the platforms that this piece of content would be posted to (Instagram, Instagram Reels, TikTok, X, LinkedIn, etc). The ideas should be engaging and suitable for a beginner audience, while also being relevant to the topic and the research findings.
    </task>
  """,
)

class NotionBlock(BaseModel):
  type: Literal["paragraph", "heading_2", "link_preview"]
  text: str
  url: Optional[str] = None

class NotionBlocks(BaseModel):
  blocks: list[NotionBlock]

text_to_json_writer = Agent(
  name="Text to JSON Content Formatter",
  instructions=f"""
    <background>
    You are a content formatter that takes text content and formats it into JSON blocks.
    </background>
    <task>
    Format the content provided to you into the defined output structure in the output type section. You are able to create blocks of type paragraph, heading_2, and link_preview. Each block should have a type and text field. If the block is a link_preview, it should also have a url field which is link to the source of the content.
    </task>
  """,
  output_type=AgentOutputSchema(NotionBlocks, strict_json_schema=True),
  model="gpt-4o-mini",
)

def convert_json_to_notion_blocks(content_blocks: NotionBlocks) -> list[dict]:

  json_content = content_blocks.blocks

  notion_blocks = []

  for item in json_content:
    if item.type == "paragraph":
      notion_blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
          "rich_text": [{"type": "text", "text": {"content": item.text}}]
        }
      })
    elif item.type == "heading_2":
      notion_blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
          "rich_text": [{"type": "text", "text": {"content": item.text}}]
        }
      })
    elif item.type == "link_preview" and 'url' in item:
      notion_blocks.append({
        "object": "block",
        "type": "link_preview",
        "link_preview": {
          "url": item.url if 'url' in item else ""
        }
      })

  return notion_blocks

def create_research_report_page(parent_id: str, topic: str, content_blocks: list):

  # Function to create a new page in Notion with the research report

  notion_blocks = convert_json_to_notion_blocks(content_blocks)

  url = "https://api.notion.com/v1/pages"
  headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
  }

  data = {
    "parent": {"page_id": parent_id},
    "properties": {
      "title": {
        "title": [
          {
            "text": {
              "content": f"Research Report on {topic}"
            }
          }
        ]
      }
    },
    "children": notion_blocks
  }

  response = requests.post(url, headers=headers, json=data)

  print(f"Creating research report page with data: {data}")

  print(f"Response status code: {response.status_code}")

  if response.status_code == 200:
    print("Research report page created successfully.")
  else:
    print(f"Failed to create research report page: {response.status_code} - {response.text}")

def create_content_ideas_page(parent_id: str, topic: str, content_blocks: list):
   
  # Function to create a new page in Notion with the content ideas

  notion_blocks = convert_json_to_notion_blocks(content_blocks)
  
  url = "https://api.notion.com/v1/pages"
  headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
  }

  data = {
    "parent": {"page_id": parent_id},
    "properties": {
      "title": {
        "title": [
          {
            "text": {
              "content": f"Content Ideas for {topic}"
            }
          }
        ]
      }
    },
    "children": notion_blocks
  }

  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Content ideas page created successfully.")
  else:
    print(f"Failed to create content ideas page: {response.status_code} - {response.text}")

# Agent Function

async def run_content_research(topic: str, page_id: str = None):

  print('starting content research...')
  # Run the research agent to get the research report
  research_result = await Runner.run(research_agent, topic)

  print("Received research result")

  # Run the content ideas agent to get content ideas based on the research

  content_ideas = await Runner.run(content_ideas_agent, research_result.final_output)

  print("Received content ideas")

  # Convert the research text to json blocks
  research_json_blocks = await Runner.run(text_to_json_writer, research_result.final_output)

  print("Converted research text to JSON blocks")

  # Create a Notion page for the research report
  create_research_report_page(page_id, topic, research_json_blocks.final_output)

  print("Created research report page in Notion")

  # Convert the content ideas text to json blocks
  content_ideas_json_blocks = await Runner.run(text_to_json_writer, content_ideas.final_output)

  print("Converted content ideas text to JSON blocks")

  create_content_ideas_page(page_id, topic, content_ideas_json_blocks.final_output)

  print("Created content ideas page in Notion")

  return True

# FastAPI Setup

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
    return api_key

@app.get("/")
def read_root(api_key: str = Depends(verify_api_key)):
  return {"message": "API is working"}


@app.post("/process")
async def run_process(request: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
  print(f"Received request: {request}")

  properties = request.get("data", {}).get("properties", {})

  if not properties or "Title" not in properties:
    raise HTTPException(status_code=400, detail="Invalid request: 'Title' property is required")
  
  topic = properties["Title"].get("title", [{}])[0].get("text", {}).get("content", "")
  page_id = request.get("data", {}).get("id", "")

  print (f"Processing topic: {topic} for page ID: {page_id}")

  if not page_id:
    raise HTTPException(status_code=400, detail="Invalid request: 'Page ID' is required")

  if not topic:
    raise HTTPException(status_code=400, detail="Invalid request: 'Title' property is required")

  # Add the task to background processing
  background_tasks.add_task(run_content_research, topic, page_id)
  
  # Return immediately
  return {"status": "processing", "message": f"Research started for topic: {topic}"}