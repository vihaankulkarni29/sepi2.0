# SEPI 2.0 - Sensitive Efflux Protein Identifier

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A versatile bioinformatics platform for the automated acquisition of reference protein sequences from NCBI. SEPI 2.0 empowers researchers to build high-quality, custom reference datasets for any bacteria and any protein set with minimal effort and maximum reproducibility.

## 🚀 Features

### Core Functionality
- **Dynamic Organism Support**: Search any NCBI-supported organism (not limited to E. coli and K. pneumoniae)
- **Flexible Protein Input**: Comma-separated lists, text files, or YAML configurations
- **Advanced Filtering**: Assembly level and BioSample metadata queries
- **Multiple Output Formats**: Individual FASTA files, multi-FASTA, enriched CSV reports, HTML summaries
- **Graceful Error Handling**: Continues processing when proteins aren't found
- **Verbose Logging**: Detailed logs for reproducibility and debugging

### New in SEPI 2.0
- ✅ Arbitrary organism input via `--organism`
- ✅ User-defined protein lists via `--protein_list`
- ✅ YAML configuration files via `--config`
- ✅ Assembly level filtering via `--assembly_level`
- ✅ BioSample metadata queries via `--biosample_query`
- ✅ Multi-FASTA output via `--multi_fasta`
- ✅ HTML reports via `--html_report`
- ✅ Enhanced CSV with protein length, source strain, and NCBI URLs

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Output Formats](#output-formats)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Internet connection (for NCBI API access)

### Install Dependencies
```bash
pip install pandas pyyaml biopython
```

### Download SEPI
```bash
git clone https://github.com/yourusername/sepi.git
cd sepi
```

## 🚀 Quick Start

### Basic Usage
```bash
python sepi.py --organism "Escherichia coli" --proteins "AcrA,AcrB" --email "your.email@example.com"
```

### Advanced Usage with Filters
```bash
python sepi.py \
  --organism "Pseudomonas aeruginosa PAO1" \
  --proteins "dnaA,recA" \
  --assembly_level complete_genome \
  --biosample_query "host=human" \
  --multi_fasta \
  --html_report \
  --output PAO1_refs \
  --email "your.email@example.com"
```

### Using Configuration File
```bash
python sepi.py --config my_config.yml
```

## 📖 Usage Examples

### Example 1: Basic Custom Run
```bash
python sepi.py \
  --organism "Pseudomonas aeruginosa PAO1" \
  --proteins "dnaA,recA" \
  --assembly_level complete_genome \
  --output PAO1_refs \
  --email "user@example.com"
```

### Example 2: Complex Run with Configuration File
```yaml
# saureus_virulence.yml
organism: "Staphylococcus aureus"
protein_list: "saureus_targets.txt"
output_name: "saureus_virulence_factors"
settings:
  assembly_level: "chromosome"
  multi_fasta: true
  html_report: true
user_email: "researcher@lab.edu"
```

```bash
python sepi.py --config saureus_virulence.yml
```

### Example 3: Protein List File
```bash
# saureus_targets.txt
Hla
Pvl
Sea
Tst
```

```bash
python sepi.py \
  --organism "Staphylococcus aureus" \
  --protein_list saureus_targets.txt \
  --output saureus_analysis \
  --email "researcher@lab.edu"
```

### Example 4: BioSample Filtering (Advanced)
**Note:** BioSample filtering requires sequences to be linked to BioSample metadata. This works best with recently sequenced clinical isolates.

```bash
# Filter for human-associated isolates
python sepi.py \
  --organism "Escherichia coli" \
  --proteins "AcrA,AcrB" \
  --biosample_query "host human" \
  --assembly_level scaffold \
  --output human_ecoli \
  --email "researcher@lab.edu"
```

**Important:** Not all protein sequences have BioSample metadata. If no results are found:
- Try without BioSample filtering first
- Use different query terms (e.g., "human" instead of "host=human")
- Consider that reference strains may not have detailed BioSample data

## ⚙️ Configuration

SEPI 2.0 supports YAML configuration files for reproducible and complex runs:

```yaml
# Complete configuration example
organism: "Escherichia coli"
proteins: "AcrA,AcrB,TolC"
output_name: "ecoli_efflux_pumps"
settings:
  assembly_level: "complete_genome"
  biosample_query: "host=human"
  multi_fasta: true
  html_report: true
user_email: "research@example.com"
```

## 📊 Output Formats

### 1. Individual FASTA Files
- One FASTA file per protein in `{output_name}_fasta_files/`
- Standard FASTA format with sequence headers

### 2. Multi-FASTA File (Optional)
- Single file containing all retrieved sequences
- Filename: `{output_name}.fasta`

### 3. Enhanced CSV Report
- Protein Name, Accession Number, Protein Length, Source Strain, NCBI URL
- Filename: `{output_name}_accessions.csv`

### 4. HTML Report (Optional)
- User-friendly summary with statistics
- Direct links to NCBI pages
- Filename: `{output_name}_report.html`

### 5. ZIP Archive
- Contains all individual FASTA files
- Filename: `{output_name}.zip`

### 6. Log File
- Detailed execution log
- Filename: `{output_name}.log`

## 🔧 API Reference

### Command Line Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--organism` | string | Target organism name (required) |
| `--proteins` | string | Comma-separated protein names |
| `--protein_list` | file | Path to protein list file |
| `--config` | file | YAML configuration file |
| `--assembly_level` | choice | Genome assembly level filter |
| `--biosample_query` | string | BioSample metadata query |
| `--output` | string | Output file base name |
| `--multi_fasta` | flag | Generate multi-FASTA file |
| `--html_report` | flag | Generate HTML report |
| `--email` | string | NCBI API email (required) |

### Assembly Level Options
- `complete_genome`: Complete genome assemblies only
- `chromosome`: Chromosome-level assemblies
- `scaffold`: Scaffold-level assemblies
- `contig`: Contig-level assemblies

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_sepi_robustness.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/yourusername/sepi.git
cd sepi
pip install -r requirements.txt
```

### Running Tests
```bash
python test_sepi_robustness.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the original SEPI tool by Gemini
- Uses NCBI Entrez API for protein sequence retrieval
- Built with Biopython, pandas, and other open-source libraries

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/sepi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/sepi/discussions)
- **Email**: For questions about usage or features

---

**SEPI 2.0** - Transforming bioinformatics research through automation and flexibility 🧬