#!/usr/bin/env python3

"""
SEPI 2.0 (Sensitive Efflux Protein Identifier)
Version: 2.0
Author: Gemini (based on PRD by Vihaan)
Date: September 4, 2025

Description:
A versatile bioinformatics platform for the automated acquisition of reference protein
sequences from NCBI. SEPI 2.0 empowers researchers to build high-quality, custom
reference datasets for any bacteria and any protein set with minimal effort and
maximum reproducibility.
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
import zipfile
from io import StringIO
from pathlib import Path

import pandas as pd
import yaml
from Bio import Entrez, SeqIO

# --- Pre-configured Protein Lists (as per PRD section 3.2) ---

PROTEIN_CONFIG = {
    "ecoli": {
        "proteins": [
            # AcrAB-TolC Pump & AcrZ
            "AcrA", "AcrB", "TolC", "AcrZ",
            # Transcriptional Regulators
            "AcrR", "MarA", "MarR", "RamA", "RamR", "SoxS", "Rob", "EnvR",
            # Other Efflux Pumps
            "AcrD", "AcrE", "AcrF", "MdtB", "MdtC"
        ],
        # Strain-specific requirements for higher accuracy
        "strain_specific": {
            "AcrA": "K-12 MG1655",
            "AcrB": "K-12 MG1655"
        },
        "organism_name": "Escherichia coli"
    },
    "klebsiella": {
        "proteins": [
            "OqxA", "OqxB", "EefA", "EefB", "EefC", "KexD", "KexE", "KexF"
        ],
        "strain_specific": {}, # No specific strains mentioned in PRD
        "organism_name": "Klebsiella pneumoniae"
    }
}

# --- Logging Configuration ---

# --- Caching Configuration ---
CACHE_DIR = Path(".sepi_cache")
CACHE_FILE = CACHE_DIR / "query_cache.json"
CACHE_EXPIRY_HOURS = 24  # Cache entries expire after 24 hours

CACHE_DIR.mkdir(exist_ok=True)

def get_cache_key(query: str) -> str:
    """Generate a cache key from the query string."""
    return hashlib.md5(query.encode()).hexdigest()

def load_cache() -> dict:
    """Load the cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: dict):
    """Save the cache to disk."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save cache: {e}")

def get_cached_result(cache_key: str) -> dict | str | None:
    """Get a cached result if it exists and hasn't expired."""
    cache = load_cache()
    if cache_key in cache:
        entry = cache[cache_key]
        if time.time() - entry['timestamp'] < CACHE_EXPIRY_HOURS * 3600:
            logging.info("Using cached result")
            return entry['result']
    return None

def set_cached_result(cache_key: str, result):
    """Cache a result."""
    try:
        cache = load_cache()
        cache[cache_key] = {
            'timestamp': time.time(),
            'result': result
        }
        save_cache(cache)
    except Exception as e:
        logging.warning(f"Failed to cache result: {e}")
        # Continue without caching rather than crashing

# --- Logging Configuration ---
def setup_logging(output_name: str):
    """Setup logging to both console and file."""
    log_filename = f"{output_name}.log"

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatters
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def search_and_fetch_protein(protein_name: str, organism: str, email: str, assembly_level: str = None, biosample_query: str = None) -> tuple[str, str, dict] | None:
    """
    Constructs a query, searches NCBI, and fetches the top protein sequence.
    Includes a fallback mechanism to relax search criteria if the initial search fails.
    Now supports arbitrary organisms and advanced filtering.
    """
    Entrez.email = email

    # Handle both legacy hardcoded organisms and new arbitrary organisms
    if organism in PROTEIN_CONFIG:
        config = PROTEIN_CONFIG[organism]
        organism_full_name = config["organism_name"]
        strain = config["strain_specific"].get(protein_name)
    else:
        # For arbitrary organisms, use the organism string directly
        organism_full_name = organism
        strain = None

    base_query_parts = [
        f'"{organism_full_name}"[Organism]',
        f'"{protein_name}"[Protein Name]',
    ]
    if strain:
        base_query_parts.insert(1, f'"{strain}"[Strain]')

    # Note: Assembly level filter will be handled separately in query construction
    # to avoid duplication and conflicts with "complete genome" filter

    # Add biosample query if specified
    if biosample_query:
        base_query_parts.append(f'({biosample_query})')
        logging.info(f"BioSample query added: {biosample_query}")

    # Define a series of queries from most to least strict
    if assembly_level:
        # When specific assembly level is requested, don't use "complete genome" filter
        queries = [
            # 1. Strict: RefSeq, specified assembly level, NOT resistance
            " AND ".join(base_query_parts + [f'("{assembly_level}"[Assembly Level])', '(srcdb_refseq[PROP])', 'NOT (resistance OR resistant OR multidrug OR hypothetical)']),
            # 2. Relaxed: RefSeq, specified assembly level (allows resistance terms)
            " AND ".join(base_query_parts + [f'("{assembly_level}"[Assembly Level])', '(srcdb_refseq[PROP])']),
            # 3. Broad: All protein DB, specified assembly level
            " AND ".join(base_query_parts + [f'("{assembly_level}"[Assembly Level])']),
            # 4. Broadest: All protein DB, no additional filters
            " AND ".join(base_query_parts)
        ]
    else:
        # Default behavior with complete genome preference
        queries = [
            # 1. Strict: RefSeq, complete genome, NOT resistance
            " AND ".join(base_query_parts + ['("complete genome"[Filter])', '(srcdb_refseq[PROP])', 'NOT (resistance OR resistant OR multidrug OR hypothetical)']),
            # 2. Relaxed: RefSeq, complete genome (allows resistance terms)
            " AND ".join(base_query_parts + ['("complete genome"[Filter])', '(srcdb_refseq[PROP])']),
            # 3. Broad: All protein DB, complete genome
            " AND ".join(base_query_parts + ['("complete genome"[Filter])']),
            # 4. Broadest: All protein DB, no genome filter
            " AND ".join(base_query_parts)
        ]

    logging.info(f"Constructed queries for '{protein_name}':")
    for i, query in enumerate(queries, 1):
        logging.info(f"  Query {i}: {query}")

    protein_id = None
    for i, query in enumerate(queries):
        cache_key = get_cache_key(f"search_{query}")
        cached_result = get_cached_result(cache_key)

        # Check cache first
        cached_result = get_cached_result(cache_key)
        if cached_result:
            logging.info(f"Using cached result for '{protein_name}'")
            return cached_result
    
        try:
            logging.info(f"Searching for '{protein_name}' (Attempt {i+1})...")
    
            handle = Entrez.esearch(db="protein", term=query, retmax=1)
            record = Entrez.read(handle)
            handle.close()
            time.sleep(0.35)  # Adhere to NCBI's limit
        except Exception as e:
            logging.error(f"An error occurred during search attempt {i+1} for '{protein_name}': {e}")
            continue # Try next query
    
        if record["IdList"]:
            protein_id = record["IdList"][0]
            logging.info(f"Found a candidate for '{protein_name}' on Attempt {i+1}.")
            break # Exit the loop once an ID is found

    if not protein_id:
        logging.warning(f"All search attempts failed for '{protein_name}'. No entry found.")
        return None

    # Fetch the record using the found ID
    try:
        # Fetch FASTA sequence (temporarily disable caching)
        fetch_handle = Entrez.efetch(db="protein", id=protein_id, rettype="fasta", retmode="text")
        fasta_data = fetch_handle.read()
        fetch_handle.close()
        time.sleep(0.35)

        fasta_io = StringIO(fasta_data)
        seq_record = SeqIO.read(fasta_io, "fasta")
        accession = seq_record.id
        protein_length = len(seq_record.seq)

        # Fetch additional metadata
        summary_handle = Entrez.esummary(db="protein", id=protein_id)
        summary_record = Entrez.read(summary_handle)
        summary_handle.close()
        time.sleep(0.35)

        # Extract metadata
        metadata = {}
        if summary_record and len(summary_record) > 0:
            record = summary_record[0]
            metadata = {
                'protein_length': protein_length,
                'source_strain': record.get('Caption', 'N/A'),  # Often contains strain info
                'ncbi_url': f"https://www.ncbi.nlm.nih.gov/protein/{protein_id}",
                'title': record.get('Title', ''),
                'organism': record.get('Organism', organism_full_name)
            }

        logging.info(f"Successfully retrieved '{protein_name}' with Accession: {accession}")

        # Cache the result
        result_to_cache = (accession, fasta_data, metadata)
        set_cached_result(cache_key, result_to_cache)

        return accession, fasta_data, metadata
    except Exception as e:
        logging.error(f"Found ID {protein_id} but failed to fetch the record for '{protein_name}': {e}")
        return None


def generate_html_report(args, results, target_proteins):
    """Generate an HTML summary report of the SEPI run."""
    total_proteins = len(target_proteins)
    successful_proteins = len(results)
    failed_proteins = total_proteins - successful_proteins

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEPI 2.0 Report - {args.output}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .stat-box {{ background-color: #e8f4f8; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }}
        .success {{ background-color: #d4edda; }}
        .warning {{ background-color: #fff3cd; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .filters {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SEPI 2.0 Run Report</h1>
        <p><strong>Output Name:</strong> {args.output}</p>
        <p><strong>Organism:</strong> {args.organism}</p>
        <p><strong>Run Date:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-box success">
            <h3>{successful_proteins}</h3>
            <p>Proteins Retrieved</p>
        </div>
        <div class="stat-box warning">
            <h3>{failed_proteins}</h3>
            <p>Proteins Not Found</p>
        </div>
        <div class="stat-box">
            <h3>{total_proteins}</h3>
            <p>Total Proteins</p>
        </div>
    </div>

    <div class="filters">
        <h3>Applied Filters</h3>
        <p><strong>Assembly Level:</strong> {args.assembly_level or 'None'}</p>
        <p><strong>BioSample Query:</strong> {args.biosample_query or 'None'}</p>
    </div>

    <h2>Retrieved Proteins</h2>
    <table>
        <thead>
            <tr>
                <th>Protein Name</th>
                <th>Accession Number</th>
                <th>Protein Length</th>
                <th>Source Strain</th>
                <th>NCBI Link</th>
            </tr>
        </thead>
        <tbody>
"""

    for result in results:
        html_content += f"""
            <tr>
                <td>{result['Protein_Name']}</td>
                <td>{result['Accession_Number']}</td>
                <td>{result['Protein_Length']}</td>
                <td>{result['Source_Strain']}</td>
                <td><a href="{result['NCBI_URL']}" target="_blank">View on NCBI</a></td>
            </tr>
"""

    html_content += """
        </tbody>
    </table>

    <div class="footer" style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
        <p><strong>SEPI 2.0</strong> - Versatile Bioinformatics Platform for Protein Sequence Retrieval</p>
        <p>Report generated automatically by SEPI 2.0</p>
    </div>
</body>
</html>
"""

    return html_content


def main():
    """Main function to parse arguments and run the SEPI workflow."""
    parser = argparse.ArgumentParser(
        description="SEPI 2.0: A versatile bioinformatics platform for automated acquisition of reference protein sequences from NCBI.",
        epilog="Example: python sepi.py --organism \"Pseudomonas aeruginosa PAO1\" --proteins \"dnaA,recA\" --assembly_level complete_genome --output PAO1_refs --email user@example.com"
    )
    parser.add_argument(
        "--organism",
        help="Specifies the target organism (e.g., \"Escherichia coli\", \"Pseudomonas aeruginosa PAO1\")."
    )
    parser.add_argument(
        "--proteins",
        type=str,
        help='A comma-separated list of protein names, or path to a .txt file containing protein names.'
    )
    parser.add_argument(
        "--protein_list",
        type=str,
        help="Path to a .txt file containing a list of protein names (one per line)."
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to a YAML configuration file containing all run parameters."
    )
    parser.add_argument(
        "--assembly_level",
        type=str,
        choices=["complete_genome", "chromosome", "scaffold", "contig"],
        help="Filter results by genome assembly level."
    )
    parser.add_argument(
        "--biosample_query",
        type=str,
        help="Additional BioSample metadata query (e.g., \"host=human\", \"collection_date=2020\")."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="SEPI_output",
        help="The base name for the output files. (Default: SEPI_output)"
    )
    parser.add_argument(
        "--multi_fasta",
        action="store_true",
        help="Generate a single multi-FASTA file containing all retrieved sequences."
    )
    parser.add_argument(
        "--html_report",
        action="store_true",
        help="Generate an HTML summary report of the run."
    )
    parser.add_argument(
        "--email",
        help="Your email address (required by NCBI for API usage)."
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.output)

    # Load configuration from YAML file if provided
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
            # Override command line args with config values
            for key, value in config.items():
                if key == 'settings':
                    for setting_key, setting_value in value.items():
                        setattr(args, setting_key, setting_value)
                elif key == 'protein_list':
                    args.protein_list = value
                elif key == 'user_email':
                    args.email = value
                elif hasattr(args, key):
                    setattr(args, key, value)
        except Exception as e:
            logging.error(f"Failed to load configuration file '{args.config}': {e}")
            sys.exit(1)

    # Validate required arguments
    if not args.organism:
        logging.error("Organism is required. Provide it via --organism or in the config file.")
        sys.exit(1)
    if not args.email:
        logging.error("Email is required. Provide it via --email or in the config file.")
        sys.exit(1)

    # Determine the list of proteins to retrieve
    target_proteins = []
    if args.protein_list:
        # Load proteins from file
        try:
            with open(args.protein_list, 'r') as f:
                target_proteins = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"Failed to load protein list file '{args.protein_list}': {e}")
            sys.exit(1)
    elif args.proteins:
        if args.proteins.lower() == "all" and args.organism in PROTEIN_CONFIG:
            target_proteins = PROTEIN_CONFIG[args.organism]["proteins"]
        else:
            target_proteins = [p.strip() for p in args.proteins.split(',')]
    else:
        # Default to "all" for legacy organisms
        if args.organism in PROTEIN_CONFIG:
            target_proteins = PROTEIN_CONFIG[args.organism]["proteins"]
        else:
            logging.error("No protein names provided for custom organism. Use --proteins or --protein_list.")
            sys.exit(1)

    if not target_proteins:
        logging.error("No protein names provided. Exiting.")
        sys.exit(1)

    logging.info(f"Starting SEPI 2.0 for organism: '{args.organism}'")
    logging.info(f"Target proteins: {', '.join(target_proteins)}")
    logging.info(f"Output file base name: '{args.output}'")
    if args.assembly_level:
        logging.info(f"Assembly level filter: {args.assembly_level}")
    if args.biosample_query:
        logging.info(f"BioSample query: {args.biosample_query}")

    # --- Workflow Execution ---
    results = []
    all_fasta_sequences = []
    output_dir = Path(f"{args.output}_fasta_files")
    output_dir.mkdir(exist_ok=True)

    for protein in target_proteins:
        fetched_data = search_and_fetch_protein(
            protein, args.organism, args.email,
            args.assembly_level, args.biosample_query
        )
        if fetched_data:
            accession, fasta_sequence, metadata = fetched_data
            result_entry = {
                "Protein_Name": protein,
                "Accession_Number": accession,
                "Protein_Length": metadata.get('protein_length', 'N/A'),
                "Source_Strain": metadata.get('source_strain', 'N/A'),
                "NCBI_URL": metadata.get('ncbi_url', f"https://www.ncbi.nlm.nih.gov/protein/{accession}")
            }
            results.append(result_entry)
            all_fasta_sequences.append(fasta_sequence)

            # Save individual FASTA file
            # Sanitize accession number to remove invalid filename characters
            safe_accession = accession.replace('|', '_').replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_')
            file_name = f"{protein}_{safe_accession}.fasta"
            file_path = output_dir / file_name
            with open(file_path, "w") as f_out:
                f_out.write(fasta_sequence)
        else:
            logging.warning(f"Skipping protein '{protein}' - not found or failed to retrieve")

    if not results:
        logging.warning("No proteins were successfully retrieved. No output files will be generated.")
        # Clean up empty directory
        try:
            os.rmdir(output_dir)
        except OSError:
            pass
        sys.exit(0)

    # --- Generate Output Files ---

    # 1. Enhanced CSV Accession Report
    csv_filename = f"{args.output}_accessions.csv"
    try:
        df = pd.DataFrame(results)
        df.to_csv(csv_filename, index=False)
        logging.info(f"Enriched accession report saved to '{csv_filename}'")
    except Exception as e:
        logging.error(f"Failed to create CSV report: {e}")

    # 2. Multi-FASTA file (if requested)
    if args.multi_fasta:
        multi_fasta_filename = f"{args.output}.fasta"
        try:
            with open(multi_fasta_filename, "w") as f_out:
                for fasta_seq in all_fasta_sequences:
                    f_out.write(fasta_seq)
            logging.info(f"Multi-FASTA file saved to '{multi_fasta_filename}'")
        except Exception as e:
            logging.error(f"Failed to create multi-FASTA file: {e}")

    # 3. HTML Report (if requested)
    if args.html_report:
        html_filename = f"{args.output}_report.html"
        try:
            html_content = generate_html_report(args, results, target_proteins)
            with open(html_filename, "w") as f_out:
                f_out.write(html_content)
            logging.info(f"HTML report saved to '{html_filename}'")
        except Exception as e:
            logging.error(f"Failed to create HTML report: {e}")

    # 4. Create ZIP Archive
    zip_filename = f"{args.output}.zip"
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for fasta_file in output_dir.glob("*.fasta"):
                zipf.write(fasta_file, arcname=fasta_file.name)
                os.remove(fasta_file) # Clean up individual file after adding to zip
        os.rmdir(output_dir) # Clean up the temporary directory
        logging.info(f"FASTA files packaged into '{zip_filename}'")
    except Exception as e:
        logging.error(f"Failed to create ZIP archive: {e}")

    logging.info("SEPI 2.0 run completed successfully.")


if __name__ == "__main__":
    main()