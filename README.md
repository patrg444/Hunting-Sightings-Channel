# Hunting Sightings Channel

An automated system that extracts animal sighting mentions from hiking trail reviews and trip reports, maps them to Colorado Game Management Units (GMUs), and delivers daily email digests.

## Project Overview

This MVP pulls wildlife sightings from various outdoor recreation websites and forums, focusing on game species (elk, deer, bear, pronghorn, bighorn sheep, mountain goat) within Colorado GMUs. The system uses keyword matching and geospatial analysis to identify and locate sightings, then compiles them into a daily email digest.

## Milestones

- **Milestone 1**: GMU polygons, trail index, and technical design (Week 1)
- **Milestone 2**: Core scrapers for 14ers, SummitPost, Reddit (Week 2)
- **Milestone 3**: Daily email digest system (Week 3)
- **Milestone 4**: Hiking Project integration and configuration system (Week 4)

## Data Sources

### Low-friction (MVP):
- 14ers.com
- SummitPost.org
- Reddit (via official API)
- FreeCampsites.net
- iOverlander
- The Trek

### Moderate effort:
- Hiking Project / Mountain Project (legacy JSON endpoints)

### Post-MVP:
- AllTrails, Gaia GPS, Backpacker.com (require permissions)

## Setup

### Prerequisites
- Python 3.9+
- PostgreSQL with PostGIS extension
- Redis (for task scheduling)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/patrg444/Hunting-Sightings-Channel.git
cd Hunting-Sightings-Channel
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

6. Initialize database:
```bash
python scripts/init_db.py
```

## Configuration

Edit `config/settings.yaml` to configure:
- Target GMUs
- Email recipients
- Scraping intervals
- Species keywords

## Usage

### Command Line Interface
```bash
# Get yesterday's sightings for specific units
python scripts/sightings_cli.py --date yesterday --units 12,201 --species elk

# Run all scrapers manually
python scripts/run_scrapers.py

# Send test email digest
python scripts/send_digest.py --test
```

### Scheduled Operations
The system runs daily scrapers via cron or systemd timers. See `docs/deployment.md` for setup.

## Project Structure
```
├── config/          # Configuration files
├── data/           # GMU polygons and trail data
├── docs/           # Documentation
├── processors/     # NLP and geospatial processing
├── scrapers/       # Web scraping modules
├── scripts/        # CLI tools and utilities
├── templates/      # Email templates
└── tests/          # Unit tests
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black .
flake8 .
```

## License

MIT License - See LICENSE file for details.

## Contact

Patrick Gloria - patrg444@gmail.com
