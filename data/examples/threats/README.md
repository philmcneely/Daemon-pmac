# Threats Endpoint Examples

This directory contains examples for the `/api/v1/threats` endpoint.

## Purpose

The threats endpoint is designed for **external threats and security concerns with impact assessment**. This aligns with the Substrate framework's structured approach to threat analysis while maintaining practical security relevance.

## Content Structure

Threat entries should follow the content/meta format and include:

### Core Components
- **Threat Category**: Type of threat (Cybersecurity, Physical, Operational, Financial, etc.)
- **Threat Level**: Severity assessment (Low, Medium, High, Critical)
- **Likelihood**: Probability of occurrence (Low, Medium, High)
- **Status**: Current monitoring state (Identified, Monitored, Active, Mitigated)

### Analysis Sections
- **Description**: Clear explanation of the threat
- **Attack Vectors**: How the threat could manifest
- **Potential Impact**: Consequences if threat materializes
- **Current Defenses**: Existing protections and controls
- **Indicators of Compromise**: Warning signs to monitor
- **Response Strategy**: Action plan if threat becomes active

### Assessment Components
- **Risk Mitigation Measures**: Proactive steps to reduce threat
- **Current Risk Assessment**: Quantified risk evaluation
- **Detection and Monitoring**: How threats are identified
- **Response Procedures**: Step-by-step response plans

### Format
Each threat should be structured as markdown content with:
- Clear threat identification and categorization
- Detailed impact assessment and scenarios
- Actionable response and mitigation plans
- Measurable risk indicators and metrics

## Example Files

- `example.md` - Comprehensive threat analysis examples covering cybersecurity, human factors, and supply chain threats
- Additional threat files can be added as needed

## Usage

These examples can be imported via:
```bash
python -m app.cli import threats path/to/threats/file.json
```

Or through the API:
```bash
POST /api/v1/threats
```

## Integration with Risk Management

Threats should connect to and inform the risk analysis in the `/api/v1/risks` endpoint, providing the external threat landscape that drives internal risk assessment and mitigation strategies.
