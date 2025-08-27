# Risks Endpoint Examples

This directory contains examples for the `/api/v1/risks` endpoint.

## Purpose

The risks endpoint is designed for **personal and professional risks with analysis and mitigation strategies**. This aligns with the Substrate framework's approach to systematic risk analysis while maintaining personal relevance.

## Content Structure

Risk entries should follow the content/meta format and include:

### Core Components
- **Risk Category**: Type of risk (Operational, Financial, Technical, Legal, Personal, etc.)
- **Probability**: Likelihood assessment (Low, Medium, High, Critical)
- **Impact**: Potential consequence severity
- **Status**: Current state (Identified, Monitored, In Progress, Mitigated, Closed)

### Analysis Sections
- **Description**: Clear explanation of the risk
- **Specific Concerns**: Detailed breakdown of risk factors
- **Current Mitigation Strategies**: Actions being taken
- **Monitoring & Early Warning Signs**: Indicators to watch
- **Response Plan**: Steps to take if risk materializes

### Format
Each risk should be structured as markdown content with clear headings and actionable information.

## Example Files

- `example.md` - Comprehensive risk analysis examples
- Additional risk files can be added as needed

## Usage

These examples can be imported via:
```bash
python -m app.cli import risks path/to/risks/file.json
```

Or through the API:
```bash
POST /api/v1/risks
```
