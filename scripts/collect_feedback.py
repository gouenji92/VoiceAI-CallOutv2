import csv
from pathlib import Path

FEEDBACK_CSV = Path('data/feedback.csv')
FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)

def append_feedback(text: str, label: str):
    """Append a user feedback row (text,label) to feedback.csv"""
    with FEEDBACK_CSV.open('a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([text, label])

if __name__ == '__main__':
    print('Append feedback demo. Use append_feedback(text,label) from code.')
