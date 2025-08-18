from utils.tender_crawler import EUTenderCrawler
import json

# Test EU TED API
import os
from utils.tender_crawler import EUTenderCrawler

# Get API key from environment variable
api_key = os.getenv('EU_TED_API_KEY', '')
if not api_key:
    print("Please set EU_TED_API_KEY environment variable")
    exit(1)

crawler = EUTenderCrawler(api_key)
print('Testing EU TED API search...')

# Search for renewable energy tenders
results = crawler.search_tenders('renewable energy', max_results=2)
print(f'Found {len(results)} tenders')

for i, tender in enumerate(results, 1):
    print(f'Tender {i}: {tender.get("title", "N/A")}')
    print(f'  Source: {tender.get("source", "N/A")}')
    print(f'  Value: {tender.get("estimated_value", "N/A")} {tender.get("currency", "")}')
    print()

print('EU TED Crawler test completed!')
