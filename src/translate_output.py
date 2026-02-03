"""Main script to translate CSV output files from English to Chinese."""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
from src.processors.translator import DeepseekTranslator
from src.utils.logger import logger
from src.config.settings import Settings


def translate_people(df: pd.DataFrame, translator: DeepseekTranslator) -> pd.DataFrame:
    """
    Translate People.csv with proper batching.

    Args:
        df: DataFrame with People data
        translator: DeepseekTranslator instance

    Returns:
        DataFrame with Chinese translation columns added
    """
    BATCH_SIZE = 10
    translated_rows = []

    # Fields to translate (excluding 'name' per requirements)
    # 由于bio字段太长，导致批量翻译JSON截断，改为逐字段翻译
    fields = ['currentRole', 'education', 'careerHistory', 'bio']

    # Replace NaN values with empty strings
    df = df.fillna("")

    logger.info(f"Translating {len(df)} people (using individual field translation to avoid JSON truncation)...")

    for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Translating People"):
        batch = df.iloc[i:i+BATCH_SIZE]

        # 直接使用逐字段翻译，避免JSON截断问题
        # 批量翻译会因为bio字段太长导致响应被截断
        for idx in range(len(batch)):
            row = batch.iloc[idx].to_dict()
            entity_name = row.get('name', '') or row.get('ChineseName', '')

            for field in fields:
                field_value = row.get(field, '')
                zh_field = f"{field}_zh"

                if field_value and isinstance(field_value, str) and field_value.strip():
                    try:
                        translation = translator.translate_field(
                            field_value,
                            field,
                            'Person',
                            entity_name
                        )
                        row[zh_field] = translation
                    except Exception as e:
                        logger.error(f"Translation failed for {entity_name}.{field}: {e}")
                        row[zh_field] = ""
                else:
                    row[zh_field] = ""

            translated_rows.append(row)

    result_df = pd.DataFrame(translated_rows)

    # Reorder columns to put Chinese translations after their English counterparts
    columns_ordered = []
    for col in df.columns:
        columns_ordered.append(col)
        if f"{col}_zh" in result_df.columns:
            columns_ordered.append(f"{col}_zh")

    # Add any remaining columns not in original df
    for col in result_df.columns:
        if col not in columns_ordered:
            columns_ordered.append(col)

    result_df = result_df[columns_ordered]

    logger.info(f"People translation complete: {len(result_df)} rows")
    return result_df


def translate_organizations(df: pd.DataFrame, translator: DeepseekTranslator) -> pd.DataFrame:
    """
    Translate Organizations.csv with proper batching.

    Args:
        df: DataFrame with Organizations data
        translator: DeepseekTranslator instance

    Returns:
        DataFrame with Chinese translation columns added
    """
    BATCH_SIZE = 10
    translated_rows = []

    # Fields to translate
    fields = ['name', 'description']

    # Replace NaN values with empty strings
    df = df.fillna("")

    logger.info(f"Translating {len(df)} organizations in batches of {BATCH_SIZE}...")

    for i in tqdm(range(0, len(df), BATCH_SIZE), desc="Translating Organizations"):
        batch = df.iloc[i:i+BATCH_SIZE]

        # Translate batch
        try:
            translated_batch = translator.translate_batch(
                batch.to_dict('records'),
                fields_to_translate=fields,
                entity_type='Organization'
            )

            translated_rows.extend(translated_batch)

        except Exception as e:
            logger.error(f"Batch {i//BATCH_SIZE + 1} failed: {e}")
            # Fallback: add empty Chinese columns
            for idx in range(len(batch)):
                original_row = batch.iloc[idx].to_dict()
                for field in fields:
                    original_row[f"{field}_zh"] = ""
                translated_rows.append(original_row)

    result_df = pd.DataFrame(translated_rows)

    # Reorder columns
    columns_ordered = []
    for col in df.columns:
        columns_ordered.append(col)
        if f"{col}_zh" in result_df.columns:
            columns_ordered.append(f"{col}_zh")

    for col in result_df.columns:
        if col not in columns_ordered:
            columns_ordered.append(col)

    result_df = result_df[columns_ordered]

    logger.info(f"Organizations translation complete: {len(result_df)} rows")
    return result_df


def translate_sectors(df: pd.DataFrame, translator: DeepseekTranslator) -> pd.DataFrame:
    """
    Translate Sectors.csv.

    Args:
        df: DataFrame with Sectors data
        translator: DeepseekTranslator instance

    Returns:
        DataFrame with Chinese translation columns added
    """
    # Fields to translate
    fields = ['name', 'description']

    # Replace NaN values with empty strings
    df = df.fillna("")

    logger.info(f"Translating {len(df)} sectors...")

    # Since there are only 9 sectors, translate in a single batch
    try:
        translated_data = translator.translate_batch(
            df.to_dict('records'),
            fields_to_translate=fields,
            entity_type='Sector'
        )

        result_df = pd.DataFrame(translated_data)

    except Exception as e:
        logger.error(f"Sectors translation failed: {e}")
        # Fallback: add empty Chinese columns
        result_df = df.copy()
        for field in fields:
            result_df[f"{field}_zh"] = ""

    # Reorder columns
    columns_ordered = []
    for col in df.columns:
        columns_ordered.append(col)
        if f"{col}_zh" in result_df.columns:
            columns_ordered.append(f"{col}_zh")

    for col in result_df.columns:
        if col not in columns_ordered:
            columns_ordered.append(col)

    result_df = result_df[columns_ordered]

    logger.info(f"Sectors translation complete: {len(result_df)} rows")
    return result_df


def translate_parties(df: pd.DataFrame, translator: DeepseekTranslator) -> pd.DataFrame:
    """
    Translate Parties.csv.

    Args:
        df: DataFrame with Parties data
        translator: DeepseekTranslator instance

    Returns:
        DataFrame with Chinese translation columns added
    """
    if len(df) == 0:
        logger.info("Parties.csv is empty, skipping translation")
        return df

    # Fields to translate
    fields = ['name', 'abbreviation']

    # Replace NaN values with empty strings
    df = df.fillna("")

    logger.info(f"Translating {len(df)} parties...")

    try:
        translated_data = translator.translate_batch(
            df.to_dict('records'),
            fields_to_translate=fields,
            entity_type='Party'
        )

        result_df = pd.DataFrame(translated_data)

    except Exception as e:
        logger.error(f"Parties translation failed: {e}")
        # Fallback: add empty Chinese columns
        result_df = df.copy()
        for field in fields:
            result_df[f"{field}_zh"] = ""

    # Reorder columns
    columns_ordered = []
    for col in df.columns:
        columns_ordered.append(col)
        if f"{col}_zh" in result_df.columns:
            columns_ordered.append(f"{col}_zh")

    for col in result_df.columns:
        if col not in columns_ordered:
            columns_ordered.append(col)

    result_df = result_df[columns_ordered]

    logger.info(f"Parties translation complete: {len(result_df)} rows")
    return result_df


def save_translated_csv(df: pd.DataFrame, output_path: Path):
    """
    Save translated DataFrame to CSV with proper encoding.

    Args:
        df: DataFrame to save
        output_path: Output file path
    """
    try:
        df.to_csv(
            output_path,
            index=False,
            encoding='utf-8-sig'  # UTF-8 with BOM for Excel compatibility
        )
        logger.info(f"Saved translated CSV to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV to {output_path}: {e}")
        raise


def generate_translation_report(stats: Dict, output_dir: Path):
    """
    Generate translation quality report.

    Args:
        stats: Translation statistics dictionary
        output_dir: Output directory for report
    """
    report_path = Settings.INTERMEDIATE_DIR / "translation_report.json"

    report = {
        "status": "completed",
        "statistics": stats,
        "output_files": [
            str(output_dir / "People_zh.csv"),
            str(output_dir / "Organizations_zh.csv"),
            str(output_dir / "Sectors_zh.csv"),
            str(output_dir / "Parties_zh.csv")
        ]
    }

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Translation report saved to {report_path}")
    except Exception as e:
        logger.error(f"Failed to save translation report: {e}")


def validate_translation_output(original_df: pd.DataFrame, translated_df: pd.DataFrame, entity_type: str):
    """
    Validate translated output.

    Args:
        original_df: Original DataFrame
        translated_df: Translated DataFrame
        entity_type: Type of entity being validated
    """
    logger.info(f"Validating {entity_type} translation...")

    # Check row count
    if len(original_df) != len(translated_df):
        logger.warning(f"{entity_type}: Row count mismatch! Original: {len(original_df)}, Translated: {len(translated_df)}")
    else:
        logger.info(f"{entity_type}: Row count matches ({len(original_df)} rows)")

    # Check for Chinese columns
    zh_columns = [col for col in translated_df.columns if col.endswith('_zh')]
    if zh_columns:
        logger.info(f"{entity_type}: Found {len(zh_columns)} Chinese columns: {zh_columns}")

        # Check for empty translations
        for col in zh_columns:
            empty_count = translated_df[col].isna().sum() + (translated_df[col] == "").sum()
            if empty_count > 0:
                logger.warning(f"{entity_type}: Column '{col}' has {empty_count} empty translations")
            else:
                logger.info(f"{entity_type}: Column '{col}' fully translated")
    else:
        logger.error(f"{entity_type}: No Chinese columns found!")


def main():
    """Main translation workflow."""
    logger.info("=" * 80)
    logger.info("Starting CSV Translation Workflow")
    logger.info("=" * 80)

    # Initialize translator
    translator = DeepseekTranslator()

    # Create output directory
    output_dir = Settings.OUTPUT_DIR / "translated"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Define CSV files to translate
    csv_files = {
        "People": Settings.OUTPUT_DIR / "People.csv",
        "Organizations": Settings.OUTPUT_DIR / "Organizations.csv",
        "Sectors": Settings.OUTPUT_DIR / "Sectors.csv",
        "Parties": Settings.OUTPUT_DIR / "Parties.csv"
    }

    # Verify all source files exist
    logger.info("\nVerifying source CSV files...")
    for name, path in csv_files.items():
        if not path.exists():
            logger.error(f"{name}.csv not found at {path}")
            raise FileNotFoundError(f"Required file not found: {path}")
        logger.info(f"[OK] {name}.csv found ({path.stat().st_size} bytes)")

    # Translate each CSV file
    try:
        # 1. Translate People.csv
        logger.info("\n" + "=" * 80)
        logger.info("1. Translating People.csv")
        logger.info("=" * 80)
        people_df = pd.read_csv(csv_files["People"], encoding='utf-8-sig')
        logger.info(f"Loaded {len(people_df)} people")
        translated_people = translate_people(people_df, translator)
        validate_translation_output(people_df, translated_people, "People")
        save_translated_csv(translated_people, output_dir / "People_zh.csv")

        # 2. Translate Organizations.csv
        logger.info("\n" + "=" * 80)
        logger.info("2. Translating Organizations.csv")
        logger.info("=" * 80)
        orgs_df = pd.read_csv(csv_files["Organizations"], encoding='utf-8-sig')
        logger.info(f"Loaded {len(orgs_df)} organizations")
        translated_orgs = translate_organizations(orgs_df, translator)
        validate_translation_output(orgs_df, translated_orgs, "Organizations")
        save_translated_csv(translated_orgs, output_dir / "Organizations_zh.csv")

        # 3. Translate Sectors.csv
        logger.info("\n" + "=" * 80)
        logger.info("3. Translating Sectors.csv")
        logger.info("=" * 80)
        sectors_df = pd.read_csv(csv_files["Sectors"], encoding='utf-8-sig')
        logger.info(f"Loaded {len(sectors_df)} sectors")
        translated_sectors = translate_sectors(sectors_df, translator)
        validate_translation_output(sectors_df, translated_sectors, "Sectors")
        save_translated_csv(translated_sectors, output_dir / "Sectors_zh.csv")

        # 4. Translate Parties.csv (if not empty)
        logger.info("\n" + "=" * 80)
        logger.info("4. Checking Parties.csv")
        logger.info("=" * 80)
        parties_df = pd.read_csv(csv_files["Parties"], encoding='utf-8-sig')
        logger.info(f"Loaded {len(parties_df)} parties")
        if len(parties_df) > 0:
            translated_parties = translate_parties(parties_df, translator)
            validate_translation_output(parties_df, translated_parties, "Parties")
            save_translated_csv(translated_parties, output_dir / "Parties_zh.csv")
        else:
            logger.info("Parties.csv is empty, creating empty translated file")
            save_translated_csv(parties_df, output_dir / "Parties_zh.csv")

        # Generate translation report
        logger.info("\n" + "=" * 80)
        logger.info("5. Generating Translation Report")
        logger.info("=" * 80)
        stats = translator.get_stats()
        logger.info(f"Translation Statistics:")
        logger.info(f"  - API Calls: {stats['api_calls']}")
        logger.info(f"  - Cache Hits: {stats['cache_hits']}")
        logger.info(f"  - Translations: {stats['translations']}")
        logger.info(f"  - Failures: {stats['failures']}")
        logger.info(f"  - Cache Size: {stats['cache_size']}")

        generate_translation_report(stats, output_dir)

        logger.info("\n" + "=" * 80)
        logger.info("Translation Workflow Complete!")
        logger.info("=" * 80)
        logger.info(f"\nTranslated files saved to: {output_dir}")
        logger.info(f"  - People_zh.csv ({len(translated_people)} rows)")
        logger.info(f"  - Organizations_zh.csv ({len(translated_orgs)} rows)")
        logger.info(f"  - Sectors_zh.csv ({len(translated_sectors)} rows)")
        logger.info(f"  - Parties_zh.csv ({len(parties_df)} rows)")

    except Exception as e:
        logger.error(f"\nTranslation workflow failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
