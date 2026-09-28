# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
from zoneinfo import ZoneInfo

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    search_recipes,
    get_recipe_details,
    add_recipe,
    get_pantry_inventory,
    add_pantry_item,
    calculate_nutrition_and_macros,
    fetch_public_recipes,
    geocode_address,
    find_nearby_places,
    find_nearby_grocery_stores,
    generate_recipe_image,
    generate_recipe_video,
    fetch_online_recipe_video,
)


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# Read Agent Engine resource ID from deployment_metadata.json if present
metadata_path = os.path.join(os.path.dirname(__file__), "..", "deployment_metadata.json")
agent_engine_resource_name = None

if os.path.exists(metadata_path):
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
    except Exception:
        pass

if not agent_engine_resource_name:
    agent_engine_resource_name = "projects/297842325579/locations/us-east1/reasoningEngines/4042110407937097728"

memory_bank_id = agent_engine_resource_name.split("/")[-1]

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

# Callback to persist user facts/preferences across sessions
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None

# Memory service for deployment / future redeploys
def get_memory_service():
    return VertexAiMemoryBankService(
        project="qwiklabs-gcp-02-78983e2eb373",
        location="us-east1",
        agent_engine_id=memory_bank_id,
    )

# Build A2UI v0.8 System Instruction Prompt
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are the Smart Recipe & Meal Coach. You help users plan meals, "
        "search for recipes in Firestore or online via public APIs and dynamic recipe search tools, manage their pantry inventory, "
        "calculate nutrition and macros, generate realistic dish images, generate short dish videos using generate_recipe_video (or fetch relevant recipe videos online via fetch_online_recipe_video), locate nearby grocery stores, "
        "When a user asks for a recipe or recipe suggestion (e.g. 'Suggest a healthy recipe for Chicken Biryani 🍳'), ALWAYS search for or fetch the recipe using search_recipes or fetch_public_recipes. NEVER say 'I couldn't find a recipe in my database or online'. The recipe tools automatically search Firestore, external public APIs, and online sources to retrieve or generate a complete, authentic healthy recipe with ingredients, cooking instructions, and macro breakdown. Always present the complete recipe warmly to the user. "
        "When calculating nutrition and macros for a dish or recipe name (e.g. 'Calculate nutrition and macros for Grilled Chicken Curry with Brown Rice'), ALWAYS call calculate_nutrition_and_macros directly with the dish name or ingredients provided. NEVER ask the user to input ingredient gram weights manually. "
        "The nutrition tool classifies foods along a Traffic Light health spectrum: 🟢 GREEN for healthy, nutrient-dense choices (e.g. grilled salmon, salads, egg whites, steamed veggies, quinoa), 🟡 AMBER for moderate choices (e.g. chicken curry with rice, pasta, beef stir fry), and 🔴 RED for unhealthy choices high in sugar, saturated fats, or deep-fried calories (e.g. Coca-Cola, sodas, cheeseburgers, fries, donuts). "
        "Always present the returned Traffic Light badge, health assessment, calories, protein, carbs, fat, and caution message clearly in your response. "
        "When responding to queries about pantry inventory (e.g. 'What is in my pantry?'), NEVER output raw JSON or Python dictionaries directly. ALWAYS format the response as a warm, human-readable bulleted list (e.g. 'Here is what you currently have in your pantry: ...') or as an A2UI card with clear item names, quantities, and categories. "
        "When a user asks for a video of a dish, meal, or recipe (e.g. 'generate a short video of chicken salad'), ALWAYS call the generate_recipe_video tool first. "
        "Priority must always be given to your own video generation capabilities (generate_recipe_video). If generate_recipe_video indicates a fallback or if additional online video searching is needed, use fetch_online_recipe_video. NEVER say 'I can't generate videos'."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    tools=[
        PreloadMemoryTool(),
        search_recipes,
        get_recipe_details,
        add_recipe,
        get_pantry_inventory,
        add_pantry_item,
        calculate_nutrition_and_macros,
        fetch_public_recipes,
        geocode_address,
        find_nearby_places,
        find_nearby_grocery_stores,
        generate_recipe_image,
        generate_recipe_video,
        fetch_online_recipe_video,
        get_current_time,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
