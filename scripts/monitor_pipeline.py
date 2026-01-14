"""Monitor pipeline progress in real-time."""
import time
import sys
import io
from pathlib import Path

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings

def monitor_progress():
    """Monitor pipeline progress by watching log file."""
    log_file = Path("C:/Users/ADMINI~1/AppData/Local/Temp/claude/d--Project-DataProcessing/tasks/b6168ba.output")

    if not log_file.exists():
        print("Log file not found. Pipeline may not be running.")
        return

    print("=" * 80)
    print("MONITORING PIPELINE PROGRESS")
    print("=" * 80)

    last_size = 0
    wikipedia_count = 0
    ai_batch_count = 0
    current_phase = "Unknown"

    while True:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            current_size = len(content)
            if current_size > last_size:
                # New content added
                new_content = content[last_size:]
                last_size = current_size

                # Parse progress
                for line in new_content.split('\n'):
                    if 'PHASE' in line:
                        if 'PHASE 1' in line:
                            current_phase = "Phase 1: Data Extraction"
                        elif 'PHASE 2' in line:
                            current_phase = "Phase 2: AI Enhancement"
                        elif 'PHASE 3' in line:
                            current_phase = "Phase 3: Entity Normalization"
                        elif 'PHASE 4' in line:
                            current_phase = "Phase 4: Validation & Export"

                        print(f"\n{'=' * 80}")
                        print(f"▶ {current_phase}")
                        print('=' * 80)

                    if 'Fetching Wikipedia data for' in line:
                        wikipedia_count += 1
                        name = line.split('Fetching Wikipedia data for')[-1].strip()
                        print(f"  Wikipedia: {wikipedia_count}/100 - {name}")

                    if 'Processing batch' in line and '/10' in line:
                        ai_batch_count += 1
                        print(f"  AI Enhancement: Batch {ai_batch_count}/10")

                    if 'PIPELINE COMPLETED SUCCESSFULLY' in line:
                        print("\n" + "=" * 80)
                        print("✓ PIPELINE COMPLETED SUCCESSFULLY!")
                        print("=" * 80)

                        # Show final stats
                        if 'Quality score' in content:
                            import re
                            match = re.search(r'Quality score: ([\d.]+)%', content)
                            if match:
                                print(f"\nQuality Score: {match.group(1)}%")

                        return True

                    if 'ERROR' in line and 'Failed to parse' not in line:
                        print(f"  ⚠ Error: {line.split('ERROR -')[-1].strip()}")

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user.")
            return False
        except Exception as e:
            print(f"\nError monitoring: {e}")
            return False

if __name__ == "__main__":
    try:
        monitor_progress()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
