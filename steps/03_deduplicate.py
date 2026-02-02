
import csv
import os

def main():
    print("Starting Deduplication (Step 3)...")
    
    input_file = os.path.join("data", "02_video_ids.csv")
    output_file = os.path.join("data", "03_unique_ids.csv")
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Run step 2 first.")
        return

    unique_ids = set()
    unique_rows = []
    
    # Read all rows
    # Assuming input is roughly sorted by date (newest first) from Step 1.
    # We want to keep the most recent view of a video.
    
    with open(input_file, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        
        for row in reader:
            vid = row['VideoID']
            if vid not in unique_ids:
                unique_ids.add(vid)
                unique_rows.append(row)
                
    print(f"Found {len(unique_ids)} unique videos out of all entries.")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)

    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
