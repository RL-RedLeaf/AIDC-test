import argparse
import concurrent.futures
import hashlib
import html
import io
import json
import logging
import re
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ("V01", "Capacity Value of Wind Power", "10.1109/TPWRS.2010.2062543", "2011", "IEEE Transactions on Power Systems", "https://durham-repository.worktribe.com/file/1543174/1/Accepted%20Journal%20Article", "pdf"),
    ("V02", "Optimized data center site selection—mesoclimatic effects on data center energy consumption and costs", "10.1007/s12053-021-09947-y", "2021", "Energy Efficiency", "https://link.springer.com/content/pdf/10.1007/s12053-021-09947-y.pdf", "pdf"),
    ("V03", "Chasing Carbon: The Elusive Environmental Footprint of Computing", "10.1109/HPCA51647.2021.00076", "2021", "IEEE HPCA", "https://arxiv.org/pdf/2011.02839", "pdf"),
    ("V04", "The Case for Energy-Proportional Computing", "10.1109/MC.2007.443", "2007", "IEEE Computer", "https://research.google/pubs/the-case-for-energy-proportional-computing/", "html"),
    ("V05", "Vulnerability of US and European electricity supply to climate change", "10.1038/nclimate1546", "2012", "Nature Climate Change", "https://www.nature.com/articles/nclimate1546.pdf", "pdf"),
    ("V06", "E-waste challenges of generative artificial intelligence", "10.1038/s43588-024-00712-6", "2024", "Nature Computational Science", "https://www.nature.com/articles/s43588-024-00712-6.pdf", "pdf"),
    ("V07", "Sustainable AI: Environmental Implications, Challenges and Opportunities", "10.48550/arXiv.2111.00364", "2022", "MLSys / arXiv author version", "https://arxiv.org/pdf/2111.00364", "pdf"),
    ("V08", "Data Centers in Virginia", "", "2024", "Virginia Joint Legislative Audit and Review Commission, Report 598", "https://jlarc.virginia.gov/pdfs/reports/Rpt598.pdf", "pdf"),
    ("V09", "Best practices for green data centres, ITU-T L.1300 (06/2014)", "", "2014", "International Telecommunication Union", "https://www.itu.int/rec/dologin_pub.asp?lang=e&id=T-REC-L.1300-201406-I!!PDF-E&type=items", "pdf"),
    ("V10", "Power Plants and Neighboring Communities", "", "accessed 2026-11-20", "US Environmental Protection Agency", "https://www.epa.gov/power-sector/power-plants-and-neighboring-communities", "html"),
    ("V11", "Clean Air Act Resources for Data Centers", "", "accessed 2026-11-20", "US Environmental Protection Agency", "https://www.epa.gov/stationary-sources-air-pollution/clean-air-act-resources-data-centers", "html"),
    ("V12", "2025 Long-Term Reliability Assessment", "", "2025 assessment edition; publication date checked in PDF", "North American Electric Reliability Corporation", "https://www.nerc.com/globalassets/our-work/assessments/nerc_ltra_2025.pdf", "pdf"),
    ("V13", "A review of data center cooling technology, operating conditions and the corresponding low-grade waste heat recovery opportunities", "10.1016/j.rser.2013.12.007", "2014", "Renewable and Sustainable Energy Reviews", "https://doi.org/10.1016/j.rser.2013.12.007", "html"),
]


def fetch(source):
    ident, title, doi, year, venue, url, expected = source
    result = dict(id=ident, title=title, doi=doi, year=year, venue=venue, url=url, checked="2026-11-20")
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (academic evidence audit)"})
        with urllib.request.urlopen(request, timeout=22) as response:
            content = response.read(26_000_001)
            result.update(http_status=response.status, final_url=response.url, content_type=response.headers.get("Content-Type"))
        if len(content) > 26_000_000:
            raise ValueError("response exceeds size limit")
        if content[:64].lstrip().startswith(b"%PDF-"):
            reader = PdfReader(io.BytesIO(content))
            texts = [" ".join((page.extract_text() or "").split()) for page in reader.pages]
            filename = ident + "_" + re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-")[:95] + ".pdf"
            path = ROOT / "01_公开原文" / filename
            if ident == "V12":
                path = ROOT / "01_公开原文" / "NERC_2025_Long-Term_Reliability_Assessment.pdf"
            if path.exists() and hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(content).digest():
                raise ValueError("existing local file differs; left untouched")
            if not path.exists():
                path.write_bytes(content)
            result.update(file=str(path.relative_to(ROOT)), pages=len(texts), bytes=len(content), sha256=hashlib.sha256(content).hexdigest(), first_page=texts[0][:1600])
            result["page_evidence"] = []
            terms = ["capacity value", "load", "data center", "data centre", "cooling", "ambient", "temperature", "flood", "seismic", "earthquake", "noise", "water", "rate", "customer", "manufactur", "embodied", "lifetime", "e-waste", "supply chain", "reliability", "wet bulb", "free cooling", "condenser", "interconnection"]
            for term in terms:
                matches = []
                for number, text in enumerate(texts, 1):
                    match = re.search(re.escape(term), text, re.I)
                    if match:
                        matches.append(dict(pdf_page=number, snippet=text[max(0, match.start() - 90):match.end() + 330]))
                    if len(matches) == 3:
                        break
                if matches:
                    result["page_evidence"].append(dict(term=term, matches=matches))
        else:
            raw = content.decode("utf-8", errors="replace")
            raw = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
            text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
            result["text"] = text[:120_000]
            result["status"] = "webpage inspected" if expected == "html" else "PDF unavailable; webpage only"
    except Exception as error:
        result["error"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    arguments = parser.parse_args()
    if not arguments.fetch:
        parser.error("pass --fetch to retrieve public sources and save evidence")
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    sys.stdout.reconfigure(encoding="utf-8")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = []
        for result in pool.map(fetch, SOURCES):
            results.append(result)
            print(result["id"], result.get("file") or result.get("status") or result.get("error"), flush=True)
    target = ROOT / "04_引文与来源" / "因素核验_新增来源与定位.json"
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
