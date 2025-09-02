# Experiments Data Examples

This directory contains examples for the "experiments" endpoint, which stores systematic experiments with hypothesis, method, and results using the content/meta format.

## Purpose

The experiments endpoint follows the Substrate framework's approach to systematic experimentation and learning. It's designed for documenting personal or professional experiments where you test hypotheses, measure outcomes, and learn from results in a structured way.

## Schema

The experiments endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with experiment details",
  "meta": {
    "title": "string (optional) - Entry title",
    "date": "string (optional) - Date in YYYY-MM-DD format",
    "tags": "array (optional) - Array of tags for categorization",
    "status": "string (optional) - Entry status (draft, running, completed, etc.)",
    "visibility": "string (optional) - public, unlisted, or private"
  }
}
```

## Example Data

The `experiments_example.json` file contains sample data showing:

1. **Personal Productivity Experiment**: Testing meditation impact on focus with measured outcomes
2. **Structured Methodology**: Clear hypothesis, method, baseline, and results tracking
3. **Quantitative and Qualitative Results**: Both measurable data and subjective observations

## Content Structure

The `content` field supports rich markdown formatting including:

- **Hypothesis**: Clear, testable prediction about expected outcomes
- **Method**: Detailed experimental procedure and measurement approach
- **Baseline Metrics**: Pre-experiment measurements for comparison
- **Results**: Week-by-week or phase-by-phase outcome tracking
- **Analysis**: Interpretation of results and lessons learned
- **Next Steps**: Follow-up experiments or implementation plans

## Meta Field Descriptions

- **title**: Display title for the experiment
- **date**: When the experiment was conducted or completed
- **tags**: Categories like ["experiment", "productivity", "health", "data-driven"]
- **status**: Experiment status (planning, running, completed, abandoned)
- **visibility**:
  - `public`: Visible to everyone
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

## Usage

### Add Experiment Data

```bash
curl -X POST "http://localhost:8000/api/v1/experiments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @experiments_example.json
```

### Get Experiment Data

```bash
# Get all experiment entries
curl "http://localhost:8000/api/v1/experiments"

# In multi-user mode, get specific user's experiments
curl "http://localhost:8000/api/v1/experiments/users/username"
```

## Privacy Levels

The experiments endpoint supports privacy filtering:

- **business_card**: No experiment details (too personal)
- **professional**: Work-related experiments only
- **public_full**: All public experiments and results
- **ai_safe**: Safe for AI assistants (removes sensitive personal data)

## Best Practices

- Start with clear, testable hypotheses
- Define measurable success criteria before beginning
- Track both quantitative metrics and qualitative observations
- Document methodology thoroughly for reproducibility
- Include baseline measurements for comparison
- Share learnings even from "failed" experiments
- Use consistent measurement approaches across similar experiments

**Examples:** `data/examples/experiments/`
