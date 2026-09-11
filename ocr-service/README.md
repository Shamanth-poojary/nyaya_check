# Legal Metrology OCR / Extraction Service

Independent image-intelligence microservice. Takes a package photo, returns
structured, compliance-ready JSON for the downstream Legal Metrology rules
engine. This service does **not** implement rule logic — it only extracts
evidence.

## Status: Phase 2 — PaddleOCR wired in

`POST /extract` validates the uploaded image, runs it through PaddleOCR
(`app/ocr/paddle.py`), and populates `rawOCR` with raw text + bbox +
confidence per detected line. No classification into named fields yet —
that's Phase 5/6/7.

The PaddleOCR engine downloads model weights the first time it runs
(needs internet access to huggingface.co / modelscope.cn / aistudio.baidu.com
/ paddle-model-ecology.bj.bcebos.com — one is enough). If none are reachable,
`/extract` still returns 200 with an empty `rawOCR` and a note in
`uncertainFields` rather than crashing.

## Run locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive Swagger UI, or:

```bash
curl -X POST http://localhost:8000/extract \
  -F "image=@test_images/clean/sample.jpg"
```

## Run tests

```bash
pytest -v
```

## Roadmap (from project plan)

| Phase | Focus |
|---|---|
| 1 | Service skeleton, `/extract`, image validation, placeholder JSON *(done)* |
| 2 | PaddleOCR: image → text + bbox + confidence |
| 3 | OpenCV: resize, contrast/CLAHE, denoise, deskew (benchmarked incrementally) |
| 4 | OCR normalization: whitespace, Unicode, contextual numeric/date correction |
| 5 | Basic field extraction: MRP, net qty, dates, manufacturer/packer/importer, consumer care |
| 6 | Commodity/category classification |
| 7 | NER for organizations/locations/address semantics |
| 8 | Visual analysis: relative font size, contrast, readability, spacing |
| 9 | Evidence preservation: raw OCR, bboxes, confidence, crops |
| 10 | Freeze JSON contract, integrate with main backend |

## Project structure

```
app/
  main.py                 FastAPI app + router registration
  routes/ocr.py            POST /extract
  preprocessing/            Phase 3 - OpenCV pipeline
  ocr/                      Phase 2 - PaddleOCR wrapper + parser
  classification/           Phase 5-7 - regex, keywords, NER, field classifier
  visual/                   Phase 8 - layout, contrast, readability, font size
  schemas/response.py       Draft response contract (freeze in Phase 10)
tests/
test_images/                Representative test set: clean/rotated/low_contrast/
                            glossy/busy_background/mixed
```
