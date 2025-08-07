# main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import List
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path
import json

app = FastAPI()

# ---------- Models ----------
class StrategyRequest(BaseModel):
    title: str
    vision: str
    mission: str
    priorities: List[str]
    opportunities: List[str]

# ---------- Health ----------
@app.get("/", response_class=PlainTextResponse)
def health():
    return "OK"

# ---------- Slide generation ----------
@app.post("/generate-slide")
def generate_slide(req: StrategyRequest):
    prs = Presentation()
    prs.slide_width = Inches(26.667)
    prs.slide_height = Inches(15)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor(0, 0, 0)

    def add_textbox(left, top, width, height, text, font_name, font_size, color, bold=False):
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = box.text_frame
        tf.clear()
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = text.upper()
        font = run.font
        font.name = font_name
        font.size = Pt(font_size)
        font.bold = bold
        font.color.rgb = color

    def add_format_box(left, top, width, height):
        box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor(0, 0, 0)
        box.line.color.rgb = RGBColor(255, 255, 255)

    # Header
    add_textbox(0.67, 0.56, 20, 0.5, "SPORTS MARKETING PORTFOLIO",
                "Avenir Next Ultra Light", 16, RGBColor(200, 200, 200))
    add_textbox(0.67, 0.92, 26.96, 0.5, f"{req.title} | ONE PAGE STRATEGY",
                "Avenir Next", 26, RGBColor(255, 255, 255))

    # Vision
    add_format_box(0.85, 1.90, 4.82, 3.02)
    add_textbox(1.04, 2.03, 4, 0.3, "VISION", "Helvetica", 16, RGBColor(255, 255, 255), True)
    add_textbox(0.98, 2.42, 4.27, 1.99, req.vision, "Helvetica", 28, RGBColor(128, 128, 128), True)

    # Mission
    add_format_box(6.21, 1.92, 19.33, 3.0)
    add_textbox(6.39, 2.05, 4, 0.3, "MISSION", "Helvetica", 16, RGBColor(255, 255, 255), True)
    add_textbox(6.49, 2.37, 19.14, 2.39, req.mission, "Montserrat", 34, RGBColor(128, 128, 128))

    # Priorities (one bar, three columns)
    add_format_box(0.88, 5.12, 24.66, 2.34)
    add_textbox(1.04, 5.35, 4, 0.3, "PRIORITIES", "Helvetica", 16, RGBColor(255, 255, 255), True)

    num_pos = [(2.34, 5.88), (10.03, 5.88), (18.84, 5.79)]
    txt_pos = [(2.34, 6.24), (10.03, 6.24), (18.84, 6.15)]
    for i, p_text in enumerate(req.priorities[:3]):
        n_left, n_top = num_pos[i]
        t_left, t_top = txt_pos[i]
        add_textbox(n_left, n_top, 1, 0.3, f"{i+1:02}", "Arial Black", 24, RGBColor(255, 255, 255))
        add_textbox(t_left, t_top, 6, 1, p_text, "Montserrat Bold", 24, RGBColor(255, 255, 255))

    # Opportunities (one box + three columns + six placeholders)
    add_format_box(0.88, 7.69, 24.66, 6.33)
    add_textbox(1.04, 7.86, 6, 0.3, "OPPORTUNITY", "Helvetica Neue", 16, RGBColor(255, 255, 255), True)

    opp_pos = [(1.55, 8.58), (10.21, 8.40), (18.19, 8.37)]
    for i, o_text in enumerate(req.opportunities[:3]):
        left, top = opp_pos[i]
        add_textbox(left, top, 6, 1, o_text, "Montserrat", 18, RGBColor(255, 255, 255))

    ph = [(1.41, 10.09), (5.02, 10.09), (9.78, 10.03),
          (13.40, 10.03), (18.18, 10.00), (21.78, 10.03)]
    for left, top in ph:
        r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(3.27), Inches(3.17))
        r.fill.background()
        r.line.color.rgb = RGBColor(200, 200, 200)
        r.line.width = Pt(1.5)

    out_path = "/tmp/Strategy_Slide.pptx"
    prs.save(out_path)
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="Strategy_Slide.pptx"
    )

# ---------- Custom OpenAPI dict (for GPT file downloads) ----------
def build_openapi_schema() -> dict:
    schema = get_openapi(
        title="Pitch Formula API",
        version="1.0.0",
        description="API for generating strategy slides",
        routes=app.routes,
    )
    # Server
    schema["servers"] = [{"url": "https://pitch-formula-slide-api.onrender.com"}]

    # Ensure 200 is a file/binary
    schema["paths"]["/generate-slide"]["post"]["responses"]["200"] = {
        "description": "PPTX file",
        "content": {
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
                "schema": {"type": "string", "format": "binary"}
            }
        },
        "x-oai-return-type": "file"
    }
    return schema

# Let FastAPI use the dict above for /openapi.json internally
app.openapi_schema = build_openapi_schema()

# Also expose it explicitly so the GPT builder can fetch it
@app.get("/openapi.json", response_class=JSONResponse)
def serve_openapi():
    return JSONResponse(content=app.openapi_schema)
