"""Live monitoring script for data processing pipeline."""
import time
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def clear_screen():
    """Clear console screen."""
    print("\033[2J\033[H", end="")

def monitor_pipeline():
    """Monitor pipeline progress in real-time."""
    intermediate_dir = Path('data/intermediate')
    ai_cache = intermediate_dir / 'ai_responses.json'

    # Find latest log file
    log_files = list(intermediate_dir.glob('processing_*.log'))
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_log = log_files[0] if log_files else None

    print("=" * 80)
    print("DATA PROCESSING PIPELINE - LIVE MONITOR")
    print("=" * 80)
    print("\nPress Ctrl+C to stop monitoring\n")

    last_batch_count = 0
    last_log_size = 0
    current_phase = "Unknown"
    iteration = 0

    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Check AI progress
            batch_count = 0
            if ai_cache.exists():
                try:
                    with open(ai_cache, 'r', encoding='utf-8') as f:
                        ai_data = json.load(f)
                    batch_count = len(ai_data)

                    if batch_count != last_batch_count:
                        progress_pct = batch_count * 100 // 68
                        print(f"\n[{timestamp}] AI Enhancement Progress:")
                        print(f"  > Batches completed: {batch_count}/68 ({progress_pct}%)")
                        print(f"  > People processed: ~{min(batch_count * 10, 100)}/100")
                        last_batch_count = batch_count
                except Exception as e:
                    print(f"[{timestamp}] Warning: Could not read AI cache - {e}")

            # Check log for new activity
            if latest_log and latest_log.exists():
                current_size = latest_log.stat().st_size
                if current_size > last_log_size:
                    try:
                        with open(latest_log, 'r', encoding='utf-8') as f:
                            f.seek(last_log_size)
                            new_lines = f.readlines()

                        for line in new_lines:
                            if 'PHASE 1' in line:
                                current_phase = "Phase 1: Data Extraction"
                            elif 'PHASE 2' in line:
                                current_phase = "Phase 2: AI Enhancement"
                            elif 'PHASE 3' in line:
                                current_phase = "Phase 3: Entity Normalization"
                            elif 'PHASE 4' in line:
                                current_phase = "Phase 4: Validation & Export"

                            if any(keyword in line for keyword in ['PHASE', 'Processing batch', 'Step', 'COMPLETED']):
                                content = line.split('INFO - ')[-1].strip() if 'INFO - ' in line else line.strip()
                                if content and not content.startswith('==='):
                                    print(f"  [{timestamp}] {content}")

                        last_log_size = current_size
                    except Exception as e:
                        print(f"[{timestamp}] Warning: Could not read log - {e}")

            # Status update every 30 seconds
            if iteration % 6 == 0:
                print(f"\n[{timestamp}] Status Update:")
                print(f"  Current Phase: {current_phase}")
                print(f"  AI Batches: {batch_count}/68")

            # Check if completed
            output_dir = Path('data/output')
            if (output_dir / 'People.csv').exists():
                print("\n" + "=" * 80)
                print("PIPELINE COMPLETED SUCCESSFULLY!")
                print("=" * 80)

                # Show output files
                print("\nGenerated files:")
                for csv_file in output_dir.glob('*.csv'):
                    size = csv_file.stat().st_size
                    print(f"  - {csv_file.name} ({size:,} bytes)")

                # Show summary if available
                summary_file = intermediate_dir / 'processing_summary.json'
                if summary_file.exists():
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary = json.load(f)
                    print(f"\nQuality Score: {summary.get('quality_score', 'N/A')}%")
                    print(f"Total People: {summary.get('total_people', 'N/A')}")
                    print(f"Total Organizations: {summary.get('total_organizations', 'N/A')}")

                break

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user.")
        print(f"Last known status:")
        print(f"  Phase: {current_phase}")
        print(f"  AI Batches: {batch_count}/68")

if __name__ == "__main__":
    try:
        monitor_pipeline()
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
