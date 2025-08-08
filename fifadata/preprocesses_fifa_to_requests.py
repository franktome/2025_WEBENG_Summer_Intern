from datetime import datetime
from collections import Counter
import re

input_file = "./data/wc_day50_1.txt"
output_file = "request.txt"

pattern = re.compile(r'\[(.*?)\]')  # [30/Apr/1998:21:30:17 +0000]

counter = Counter()

# encoding='latin-1' 로 열기 (cp949 대신)
with open(input_file, "r", encoding="latin-1", errors="ignore") as f:
    for line in f:
        m = pattern.search(line)
        if not m:
            continue
        dt = datetime.strptime(m.group(1), "%d/%b/%Y:%H:%M:%S %z")
        ts = int(dt.timestamp())
        counter[ts] += 1

start = min(counter.keys())
end = max(counter.keys())
interval = 60  # 60초 단위

time_buckets = []
current = start
while current <= end:
    count = sum(c for t, c in counter.items() if current <= t < current + interval)
    time_buckets.append(count)
    current += interval

with open(output_file, "w") as f:
    for c in time_buckets:
        f.write(f"{c}\n")

print(f"Saved {len(time_buckets)} lines to {output_file}")
