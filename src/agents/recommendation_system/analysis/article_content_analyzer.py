"""
Resource Content Understanding (Section 24) - Articles & Research Papers.

Piece 1: fetching a resource's REAL content (not just a search snippet) and
extracting readable text from it -- either a normal web page (HTML) or a
downloadable PDF (common for research papers, e.g. arXiv).
Piece 2: sending that real text to Gemini and getting back a structured
section-by-section breakdown of what the article/paper actually covers.

HONEST NOTE: many articles are freely readable (this works well), but many
research papers and most books sit behind paywalls or access restrictions.
When that happens, this returns a clear "not accessible" status instead of
pretending to have read something it couldn't.
"""

import io
import os
import json

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from google import genai

REQUEST_TIMEOUT_SECONDS = 10
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EduTwinRecommendationEngine/1.0"}
GEMINI_MODEL = "gemini-3.5-flash"
MAX_CONTENT_CHARACTERS = 30000


def is_pdf_url(url, response):
    """
    Decides whether a URL points to a PDF, using both the URL itself and
    the server's own claim about what it's sending back.

    Args:
        url (str): the resource URL.
        response (requests.Response): the already-fetched response.

    Returns:
        bool: True if this looks like a PDF.
    """
    if url.lower().endswith(".pdf"):
        return True

    content_type = response.headers.get("Content-Type", "")

    return "application/pdf" in content_type.lower()


def extract_html_text(html_content):
    """
    Pulls just the readable text out of a raw HTML page, discarding
    navigation, scripts, styling, and other non-content clutter.

    Args:
        html_content (str): raw HTML.

    Returns:
        str: plain readable text.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    for unwanted in soup(["script", "style", "nav", "header", "footer"]):
        unwanted.decompose()

    text = soup.get_text(separator="\n", strip=True)

    return text


def extract_pdf_text(pdf_bytes):
    """
    Extracts readable text from raw PDF file bytes.

    Args:
        pdf_bytes (bytes): the raw content of a PDF file.

    Returns:
        str: plain text extracted from every page, combined.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []

    for page in reader.pages:
        pages_text.append(page.extract_text())

    return "\n".join(pages_text)


def fetch_resource_content(url):
    """
    Fetches a resource's real content and extracts readable text from it,
    handling both normal web pages and PDFs.

    Args:
        url (str): the resource's URL.

    Returns:
        tuple: (text, access_status)
            text: the extracted readable text, or None if unavailable.
            access_status: "ok" if it worked, or a clear reason it didn't.
    """
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers=REQUEST_HEADERS)

        if response.status_code >= 400:
            return None, f"Page returned an error (status code {response.status_code})."

        if is_pdf_url(url, response):
            text = extract_pdf_text(response.content)
        else:
            text = extract_html_text(response.text)

        if not text.strip():
            return None, "Page loaded, but no readable text could be extracted (may require login or JavaScript)."

        return text, "ok"
    except requests.exceptions.RequestException as error:
        return None, f"Content not accessible: {error}"


def build_section_prompt(content_text, topic):
    """
    Builds the instruction sent to Gemini, asking it to break the content
    into topic sections and flag which ones relate to the learner's topic.

    Args:
        content_text (str): extracted readable text (output of fetch_resource_content).
        topic (str): the topic the learner is actually interested in.

    Returns:
        str: the full prompt.
    """
    truncated_text = content_text[:MAX_CONTENT_CHARACTERS]

    return f"""You are analyzing the text of an article or research paper to identify its distinct sections.

Read the content below and split it into sections, where each section covers one coherent idea or topic.

For each section, note whether it is directly relevant to this specific topic the reader cares about: "{topic}"

Respond with ONLY a JSON array, no other text, no markdown code fences. Each item must have this exact shape:
{{"section_number": 1, "heading": "short section title", "summary": "one sentence describing what is covered", "relevant_to_requested_topic": true}}

Content:
{truncated_text}
"""


def call_gemini(prompt):
    """
    Sends a prompt to Gemini and returns its raw text response.

    Args:
        prompt (str): the full prompt to send.

    Returns:
        tuple: (response_text, status) -- response_text is None on failure.
    """
    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key is None:
        return None, "GEMINI_API_KEY environment variable is not set."

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text, "ok"
    except Exception as error:
        return None, f"Gemini API call failed: {error}"


def parse_gemini_json_response(response_text):
    """
    Safely parses Gemini's response as JSON, stripping markdown code fences
    if the model added them despite being told not to.

    Args:
        response_text (str): raw text from the Gemini response.

    Returns:
        list or None: parsed sections, or None if parsing failed.
    """
    cleaned = response_text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as error:
        print(f"[article content] Could not parse Gemini's response as JSON ({error}).")
        return None


def analyze_article_content(url, topic):
    """
    The full pipeline: URL -> real content -> Gemini section breakdown.

    This is the ONLY function other parts of the engine need to call --
    everything else in this file is an internal step it uses.

    Args:
        url (str): the article/paper's URL.
        topic (str): the topic the learner actually cares about, so Gemini
              can flag which sections are directly relevant.

    Returns:
        dict: {"access_status": "ok" or a clear reason it failed, "sections": [...] or None}
    """
    content_text, fetch_status = fetch_resource_content(url)

    if content_text is None:
        return {"access_status": fetch_status, "sections": None}

    prompt = build_section_prompt(content_text, topic)
    response_text, gemini_status = call_gemini(prompt)

    if response_text is None:
        return {"access_status": gemini_status, "sections": None}

    sections = parse_gemini_json_response(response_text)

    if sections is None:
        return {"access_status": "Gemini responded, but its answer could not be parsed.", "sections": None}

    return {"access_status": "ok", "sections": sections}


if __name__ == "__main__":
    print("=== Testing HTML extraction (synthetic, no network needed) ===")
    fake_html = """
    <html>
      <head><style>.hidden { display: none; }</style></head>
      <body>
        <nav>Home | About | Contact</nav>
        <h1>Introduction to Machine Learning</h1>
        <p>Machine learning is a method of teaching computers to learn from data.</p>
        <script>console.log('tracking pixel');</script>
        <footer>Copyright 2026</footer>
      </body>
    </html>
    """
    extracted = extract_html_text(fake_html)
    print(extracted)

    print()
    print("=== Testing PDF extraction (synthetic, no network needed) ===")
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)

    reader = PdfReader(buffer)
    print(f"Created a test PDF with {len(reader.pages)} page(s) (blank, so no text expected).")

    print()
    print("=== Testing full pipeline on a real article ===")
    test_url = "https://en.wikipedia.org/wiki/Machine_learning"
    result = analyze_article_content(test_url, topic="machine learning")

    print(f"Access status: {result['access_status']}")

    if result["sections"] is not None:
        for section in result["sections"]:
            relevance = "RELEVANT" if section["relevant_to_requested_topic"] else "not directly relevant"
            print(f"{section['section_number']}. {section['heading']} ({relevance})")
            print(f"   {section['summary']}")