import csv

def add_new_addresses():
    print("🌙 MoonDev's Address Adder Starting Up! 🚀")
    
    # Read existing addresses to avoid duplicates
    existing_addresses = set()
    with open('csvs/cut_following.csv', 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            existing_addresses.add(row['wallet_address'])
    
    print(f"📊 Found {len(existing_addresses)} existing addresses")
    
    # Read new addresses
    new_addresses = []
    with open('data/new_ppl.txt', 'r') as f:
        new_addresses = [line.strip() for line in f if line.strip()]
    
    print(f"🆕 Found {len(new_addresses)} new addresses to process")
    
    # Append new addresses to CSV
    added_count = 0
    with open('csvs/cut_following.csv', 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for addr in new_addresses:
            if addr not in existing_addresses:
                row = [
                    f"https://gmgn.ai/sol/address/{addr}",
                    addr,
                    f"https://solscan.io/account/{addr}",
                    ""
                ]
                writer.writerow(row)
                added_count += 1
    
    print(f"✨ MoonDev's Script Complete! Added {added_count} new addresses! ✨")
    print("🌜 Thanks for using MoonDev's Address Adder! 🌛")

if __name__ == "__main__":
    add_new_addresses()

