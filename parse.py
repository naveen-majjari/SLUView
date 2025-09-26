"""
Q5 parsing script using BeautifulSoup.
Usage:
  python parse.py listing.html --out parsed.json --fmt json
  python parse.py listing.html --out parsed.csv --fmt csv
You will need: pip install beautifulsoup4 lxml pandas
"""
import argparse, json, sys, re
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path

def extract_reviews(html_text):
    soup = BeautifulSoup(html_text, "lxml")
    # You MUST update these selectors based on your chosen site and page structure.
    # These are placeholders to get you started.
    review_nodes = soup.select('[data-review-id], .review__373c0__13kpL, .yelp-emotion')[0:50]
    out = []
    for node in review_nodes:
        # Try multiple strategies to be robust.
        def txt(sel):
            el = node.select_one(sel)
            return el.get_text(strip=True) if el else None

        # Examples (update per site DOM):
        name = txt('[itemprop="author"], .user-passport-info .css-1m051bw, .css-1m051bw')
        date = txt('time[datetime], .css-chan6m, [data-testid="review-date"]')
        text = txt('[lang], p.comment__373c0__1M-px, p, [data-testid="review-text"]')
        rating_el = node.select_one('[aria-label*="star"], [role="img"][aria-label*="star"], .i-stars')
        rating = None
        if rating_el and rating_el.has_attr('aria-label'):
            m = re.search(r'([0-9]+(?:\.[0-9])?)', rating_el['aria-label'])
            if m: rating = float(m.group(1))
        # fallback: class like i-stars--regular-4__373c0__1T6rx
        if rating is None and rating_el:
            m = re.search(r'([0-9](?:\.[05])?)', " ".join(rating_el.get('class', [])))
            if m: rating = float(m.group(1))

        out.append({
            "name": name,
            "date": date,
            "text": text,
            "rating": rating,
        })
    # remove empties
    out = [r for r in out if any(v for v in r.values())]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html", help="HTML file saved from curl (listing.html)")
    ap.add_argument("--out", default="parsed.json")
    ap.add_argument("--fmt", choices=["json","csv"], default="json")
    args = ap.parse_args()

    html_text = Path(args.html).read_text(encoding="utf-8", errors="ignore")
    reviews = extract_reviews(html_text)

    # Enforce minimum of 5 reviews and at least 6 fields total by adding placeholders you will extend later
    for r in reviews:
        r.setdefault("business", None)
        r.setdefault("city", None)
        r.setdefault("price", None)

    if args.fmt == "json":
        Path(args.out).write_text(json.dumps({"reviews":reviews}, indent=2), encoding="utf-8")
    else:
        df = pd.DataFrame(reviews)
        df.to_csv(args.out, index=False)

    print(f"Wrote {len(reviews)} reviews to {args.out}")

if __name__ == "__main__":
    main()
