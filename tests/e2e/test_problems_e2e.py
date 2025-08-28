"""
Module: tests.e2e.test_problems_e2e
Description: End-to-end tests for problems endpoint with markdown content support

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/e2e/test_problems_e2e.py -v

Notes:
    - Complete workflow testing with database integration
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import pytest
from fastapi.testclient import TestClient
from httpx import Response


class TestProblemsEndpoint:
    """Test suite for problems endpoint functionality"""

    def test_problems_create_basic(self, client: TestClient, auth_headers):
        """Test creating a basic problem entry"""
        problem_data = {
            "content": "### Problem: Reducing newsletter churn\n\n- **Observed**: 8% monthly churn rate\n- **Hypothesis**: Onboarding sequence lacks value framing\n- **Next steps**: Redesign welcome email series\n\n#### Research findings\n> Initial analysis shows users drop off after the 3rd email\n\n#### Proposed solutions\n1. Add value proposition in email #2\n2. Include case studies in email #3\n3. Add interactive survey in email #4",
            "meta": {
                "title": "Newsletter Churn Problem",
                "tags": ["product", "retention", "email"],
                "priority": "high",
                "visibility": "private",
            },
        }

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        assert "id" in response_data
        assert response_data["data"]["content"] == problem_data["content"]
        assert response_data["data"]["meta"]["title"] == "Newsletter Churn Problem"
        assert "product" in response_data["data"]["meta"]["tags"]
        assert response_data["data"]["meta"]["visibility"] == "private"

    def test_problems_markdown_formatting(self, client: TestClient, auth_headers):
        """Test comprehensive markdown formatting in problem descriptions"""
        problem_data = {
            "content": """### Problem: API Performance Degradation

## Context
Our API response times have increased by **40%** over the last month.

## Symptoms
- Average response time: `250ms` → `350ms`
- 95th percentile: `500ms` → `800ms`
- Error rate: `0.1%` → `0.3%`

## Investigation Timeline

| Date | Action | Result |
|---|---|---|
| 2025-01-05 | Added monitoring | Identified DB bottleneck |
| 2025-01-06 | Query optimization | 10% improvement |
| 2025-01-07 | Index analysis | Found missing indexes |

## Code Analysis

```python
# Problematic query
users = session.query(User).filter(
    User.created_at > datetime.now() - timedelta(days=30)
).all()

# Optimized version
users = session.query(User).filter(
    User.created_at > datetime.now() - timedelta(days=30)
).options(selectinload(User.profile)).all()
```

## Root Cause Hypothesis
> Database connection pool exhaustion during peak hours

### Evidence
1. Connection pool metrics show 100% utilization
2. Query execution times correlate with pool saturation
3. Recovery happens after connection timeout

## Next Steps
- [ ] Increase connection pool size from 10 to 25
- [ ] Implement connection pooling monitoring
- [ ] Add circuit breaker pattern for DB calls
- [ ] Set up automated scaling triggers

---
*Priority: **Critical*** | *Status: **Active Investigation***""",
            "meta": {
                "title": "API Performance Investigation",
                "tags": ["performance", "database", "api", "critical"],
                "status": "solving",
                "domain": "engineering",
                "visibility": "unlisted",
            },
        }

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200

        # Verify markdown content preservation
        response_data = response.json()
        content = response_data["data"]["content"]
        assert "### Problem: API Performance Degradation" in content
        assert "```python" in content
        assert "| Date | Action | Result |" in content
        assert "> Database connection pool exhaustion" in content
        assert "- [ ] Increase connection pool size" in content

    def test_problems_list_all(self, client: TestClient, auth_headers):
        """Test retrieving all problems"""
        # Create multiple problems
        problems = [
            {
                "content": "### Problem: User Onboarding\n\nUsers struggle with initial setup process",
                "meta": {"title": "Onboarding Issue"},
            },
            {
                "content": "### Problem: Mobile Performance\n\nApp loading times on mobile devices",
                "meta": {"title": "Mobile Speed"},
            },
        ]

        problem_ids = []
        for problem in problems:
            response = client.post(
                "/api/v1/problems", json=problem, headers=auth_headers
            )
            assert response.status_code == 200
            problem_ids.append(response.json()["id"])

        # Retrieve all problems
        response = client.get("/api/v1/problems", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert "items" in response_data
        problems_list = response_data["items"]
        assert len(problems_list) >= 2

        # Verify problem data
        titles = [
            p["meta"]["title"] for p in problems_list if p.get("meta", {}).get("title")
        ]
        assert "Onboarding Issue" in titles
        assert "Mobile Speed" in titles

    def test_problems_get_single(self, client: TestClient, auth_headers):
        """Test retrieving a single problem by ID"""
        problem_data = {
            "content": "### Problem: Security Vulnerability\n\n**Issue**: SQL injection vulnerability in user search\n**Severity**: Critical\n**Discovery**: Security audit 2025-01-09",
            "meta": {
                "title": "SQL Injection Fix",
                "tags": ["security", "critical", "sql"],
                "status": "solving",
            },
        }

        # Create problem
        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200
        problem_id = response.json()["id"]

        # Retrieve single problem
        response = client.get(f"/api/v1/problems/{problem_id}", headers=auth_headers)
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["id"] == problem_id
        assert "SQL injection vulnerability" in response_data["content"]
        assert response_data["meta"]["title"] == "SQL Injection Fix"
        assert "security" in response_data["meta"]["tags"]

    def test_problems_update(self, client: TestClient, auth_headers):
        """Test updating a problem"""
        # Create initial problem
        initial_data = {
            "content": "### Problem: Database Backup\n\nDaily backups are failing intermittently",
            "meta": {"title": "Backup Failures"},
        }

        response = client.post(
            "/api/v1/problems", json=initial_data, headers=auth_headers
        )
        assert response.status_code == 200
        problem_id = response.json()["id"]

        # Update problem with solution progress
        updated_data = {
            "content": """### Problem: Database Backup (RESOLVED)

#### Original Issue
Daily backups were failing intermittently due to disk space limitations.

#### Root Cause
- Backup retention policy kept 90 days of backups
- Daily backup size grew from 2GB to 8GB over 6 months
- Available disk space: 500GB (insufficient for 90 * 8GB)

#### Solution Implemented
1. ✅ Updated retention policy to 30 days
2. ✅ Implemented backup compression (reduced size by 60%)
3. ✅ Added disk space monitoring alerts
4. ✅ Set up automated cleanup scripts

#### Results
- Backup success rate: 100% for 14 days
- Disk usage reduced from 95% to 45%
- Backup time reduced by 30% due to compression

**Status**: SOLVED ✅""",
            "meta": {
                "title": "Database Backup Failures (RESOLVED)",
                "status": "solved",
                "tags": ["database", "backup", "infrastructure", "resolved"],
                "solution_date": "2025-01-09",
            },
        }

        response = client.put(
            f"/api/v1/problems/{problem_id}", json=updated_data, headers=auth_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        assert "RESOLVED" in response_data["data"]["content"]
        assert "✅ Updated retention policy" in response_data["data"]["content"]
        assert "resolved" in response_data["data"]["meta"]["tags"]

    def test_problems_delete(self, client: TestClient, auth_headers):
        """Test deleting a problem"""
        problem_data = {
            "content": "### Problem: Temporary Issue\n\nThis problem is no longer relevant",
            "meta": {"title": "Temp Problem"},
        }

        # Create problem
        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200
        problem_id = response.json()["id"]

        # Delete problem
        response = client.delete(f"/api/v1/problems/{problem_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f"/api/v1/problems/{problem_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_problems_html_entities_handling(self, client: TestClient, auth_headers):
        """Test proper handling of HTML entities in problem content"""
        problem_data = {
            "content": "### Problem: HTML &amp; JavaScript Issues\n\n&lt;script&gt; tags are being escaped incorrectly\n\n**Code example:**\n```html\n&lt;div class=&quot;problem&quot;&gt;\n  &lt;p&gt;User input: &amp;quot;special characters&amp;quot;&lt;/p&gt;\n&lt;/div&gt;\n```",
            "meta": {
                "title": "HTML Entity Problem",
                "tags": ["html", "javascript", "escaping"],
            },
        }

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        content = response_data["data"]["content"]

        # Verify HTML entities are properly unescaped
        assert "HTML & JavaScript Issues" in content
        assert "<script>" in content
        assert '<div class="problem">' in content
        assert "&quot;special characters&quot;" in content

    def test_problems_create_empty_content_error(
        self, client: TestClient, auth_headers
    ):
        """Test validation error for empty content"""
        problem_data = {"content": "", "meta": {"title": "Empty Problem"}}

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 400

    def test_problems_create_validation_error_missing_content(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when content is missing"""
        problem_data = {
            "meta": {"title": "No Content Problem"},
        }

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 400

    def test_problems_privacy_controls(self, client: TestClient, auth_headers):
        """Test privacy controls for problems"""
        # Create private problem
        private_problem = {
            "content": "### Problem: Internal Security Issue\n\nSensitive internal problem that should not be public",
            "meta": {
                "title": "Security Problem",
                "visibility": "private",
                "tags": ["security", "internal"],
            },
        }

        response = client.post(
            "/api/v1/problems", json=private_problem, headers=auth_headers
        )
        assert response.status_code == 200
        private_id = response.json()["id"]

        # Create public problem
        public_problem = {
            "content": "### Problem: General UX Issue\n\nPublic problem that can be shared",
            "meta": {
                "title": "UX Problem",
                "visibility": "public",
                "tags": ["ux", "public"],
            },
        }

        response = client.post(
            "/api/v1/problems", json=public_problem, headers=auth_headers
        )
        assert response.status_code == 200
        public_id = response.json()["id"]

        # Verify both problems exist in authenticated list
        response = client.get("/api/v1/problems", headers=auth_headers)
        assert response.status_code == 200
        problems = response.json()["items"]
        problem_ids = [str(p["id"]) for p in problems]
        assert str(private_id) in problem_ids
        assert str(public_id) in problem_ids

    def test_problems_complex_tracking_scenario(self, client: TestClient, auth_headers):
        """Test complex problem tracking with multiple phases"""
        problem_data = {
            "content": """### Problem: Customer Support Response Time

## Problem Statement
Customer support response times have increased significantly, leading to customer dissatisfaction and potential churn.

## Metrics & KPIs
- **Current avg response time**: 4.2 hours (target: < 2 hours)
- **Customer satisfaction**: 3.2/5 (down from 4.1/5)
- **Ticket volume**: +35% over last quarter
- **Resolution time**: 18.6 hours (target: < 12 hours)

## Impact Analysis
### Business Impact
- 15% increase in customer complaints
- 8% increase in churn rate
- Estimated revenue impact: $45k/month

### Customer Segments Affected
| Segment | Impact Level | Response Time |
|---|---|---|
| Enterprise | High | 6.1 hours |
| SMB | Medium | 4.8 hours |
| Starter | Low | 3.9 hours |

## Investigation Timeline

### Phase 1: Data Collection (Jan 1-3)
- [x] Audit current ticket routing system
- [x] Analyze agent workload distribution
- [x] Review customer feedback patterns
- [x] Benchmark against industry standards

### Phase 2: Root Cause Analysis (Jan 4-6)
- [x] Identified understaffing in Tier 1 support
- [x] Found inefficient ticket categorization
- [x] Discovered knowledge base gaps
- [ ] Agent training assessment (in progress)

### Phase 3: Solution Design (Jan 7-10)
- [ ] Hiring plan for 3 additional agents
- [ ] Redesign ticket routing algorithm
- [ ] Knowledge base enhancement project
- [ ] Agent performance improvement program

## Hypothesis
> **Primary hypothesis**: The combination of increased ticket volume and inefficient routing is creating bottlenecks that compound response delays.

### Supporting Evidence
1. **Queue analysis**: 40% of tickets require escalation (industry avg: 15%)
2. **Agent utilization**: Tier 1 agents at 95% capacity vs recommended 80%
3. **Knowledge gaps**: 25% of tickets lack proper documentation

## Solution Framework

### Immediate Actions (Week 1)
```
1. Redistribute high-performing agents across shifts
2. Implement emergency escalation process
3. Create urgent ticket fast-track system
4. Daily standups for support team leads
```

### Short-term Solutions (Month 1)
- Hire 2 additional Tier 1 agents
- Implement AI-powered ticket categorization
- Launch agent training bootcamp
- Deploy customer self-service improvements

### Long-term Solutions (Months 2-3)
- Complete support team expansion (5 new hires)
- Launch advanced knowledge management system
- Implement predictive analytics for ticket volume
- Establish 24/7 support coverage

## Success Metrics
- Response time < 2 hours (current: 4.2h)
- Resolution time < 12 hours (current: 18.6h)
- Customer satisfaction > 4.0/5 (current: 3.2/5)
- Escalation rate < 20% (current: 40%)

## Stakeholders
- **Executive Sponsor**: Sarah Chen (VP Customer Success)
- **Project Lead**: Mike Rodriguez (Support Manager)
- **Technical Lead**: Alex Kim (Engineering)
- **Budget Approval**: Finance Team

---
**Next Review**: January 15, 2025
**Status**: Phase 2 (Root Cause Analysis) - 80% complete""",
            "meta": {
                "title": "Customer Support Response Time Crisis",
                "tags": [
                    "customer-support",
                    "performance",
                    "operations",
                    "high-priority",
                ],
                "status": "researching",
                "visibility": "unlisted",
            },
        }

        response = client.post(
            "/api/v1/problems", json=problem_data, headers=auth_headers
        )
        assert response.status_code == 200

        response_data = response.json()
        content = response_data["data"]["content"]

        # Verify complex content elements
        assert "Customer Support Response Time" in content
        assert "## Metrics & KPIs" in content
        assert "| Segment | Impact Level | Response Time |" in content
        assert "### Phase 1: Data Collection" in content
        assert "- [x] Audit current ticket routing" in content
        assert "```" in content  # Code block
        assert "> **Primary hypothesis**" in content  # Blockquote
        assert "**Next Review**: January 15, 2025" in content

        # Verify metadata (only standard fields are preserved)
        meta = response_data["data"]["meta"]
        assert meta["title"] == "Customer Support Response Time Crisis"
        assert "customer-support" in meta["tags"]
        assert meta["visibility"] == "unlisted"
