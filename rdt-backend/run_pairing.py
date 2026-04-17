from pairing import run_pairing

def main():
    id_pairs = run_pairing()

    if not id_pairs:
        print("Not enough active users to pair this week, skipping.")
        return

    print(f"Pairing complete: {len(id_pairs)} pairs this week.")

if __name__ == "__main__":
    main()