"""
G2 advanced: multi-page scraper using requests + BeautifulSoup.
Usage:
  python crawler.py --start "https://www.yelp.com/biz/REPLACE-ME/reviews" --pages 3 --out reviews.json
You will need: pip install requests beautifulsoup4 lxml
Only fetch your single chosen listing's paginated review pages. Be polite and throttle.
"""
import argparse, time, json, sys, re, urllib.parse as up
import requests
from bs4 import BeautifulSoup
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

def get(url, cookies=None):
    resp = requests.get(url, headers={"User-Agent": UA, "Accept-Language":"en-US,en;q=0.9"}, cookies=cookies, timeout=20)
    resp.raise_for_status()
    return resp

def parse_reviews(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for node in soup.select('[data-review-id], .review__373c0__13kpL, [data-testid="review"]'):
        def txt(sel):
            el = node.select_one(sel)
            return el.get_text(strip=True) if el else None
        name = txt('[itemprop="author"], [data-testid="reviewer-name"], .css-1m051bw')
        date = txt('time[datetime], [data-testid="review-date"]')
        text = txt('[data-testid="review-text"], [lang], p')
        rating = None
        rimg = node.select_one('[aria-label*="star"], [role="img"][aria-label*="star"]')
        if rimg and rimg.has_attr('aria-label'):
            m = re.search(r'([0-9]+(?:\.[0-9])?)', rimg['aria-label'])
            if m: rating = float(m.group(1))
        out.append({"name":name,"date":date,"text":text,"rating":rating})
    return [r for r in out if any(v for v in r.values())]

def find_next_page(url, html):
    soup = BeautifulSoup(html, "lxml")
    # Try common pagination patterns; you must adapt to your listing/site.
    a = soup.find("a", attrs={"rel":"next"}) or soup.find("a", string=re.compile(r'Next', re.I))
    if a and a.has_attr("href"):
        return up.urljoin(url, a["href"])
    # Yelp often uses offset in query (?start=20). Try to increment if seen.
    u = up.urlparse(url)
    q = dict(up.parse_qsl(u.query))
    if "start" in q:
        try:
            start = int(q["start"])
            q["start"] = str(start + 20)
            return up.urlunparse((u.scheme,u.netloc,u.path, u.params, up.urlencode(q), u.fragment))
        except: pass
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="Start URL of chosen listing reviews page")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--sleep", type=float, default=2.0, help="Seconds between requests (be polite)")
    ap.add_argument("--out", default="reviews.json")
    args = ap.parse_args()

    url = args.start
    all_reviews = []
    cookies = None

    for i in range(args.pages):
        print(f"[{i+1}/{args.pages}] GET {url}")
        resp = get(url, cookies=cookies)
        cookies = resp.cookies
        page_reviews = parse_reviews(resp.text)
        print(f"  + {len(page_reviews)} reviews")
        all_reviews.extend(page_reviews)
        nxt = find_next_page(url, resp.text)
        if not nxt:
            print("No next page found, stopping.")
            break
        url = nxt
        time.sleep(args.sleep)

    # basic de-dup by (name,date,text)
    seen = set()
    uniq = []
    for r in all_reviews:
        key = (r.get("name"), r.get("date"), (r.get("text") or "")[:80])
        if key in seen: continue
        seen.add(key)
        uniq.append(r)

    Path(args.out).write_text(json.dumps({"reviews":uniq}, indent=2), encoding="utf-8")
    print(f"Wrote {len(uniq)} total reviews -> {args.out}")

if __name__ == "__main__":
    main()
