const COMMIT_SHA = '6f8de1374b6950be2a6dd72ab1c59459b8d4e2a1'

function makeEvidence(coverageState) {
  return [
    {
      id: 'demo-evidence-fastapi-route',
      contract_version: '0.1',
      canonical_skill_id: 'fastapi',
      rule_id: 'python.fastapi.route_decorator',
      detector_version: '0.1.0',
      repository: 'github:octocat/skillproof-demo',
      commit_sha: COMMIT_SHA,
      path: 'backend/app/main.py',
      content_hash: 'bfe42e2f2ea512ef873355f6309724107a50ad6d14c18d97f7e042d8645c37df',
      start_line: 18,
      end_line: 21,
      redacted_excerpt:
        '@app.get("/health")\nasync def health():\n    return {"status": "ok"}',
      evidence_kind: 'route',
      confidence: 'high',
      coverage_state: coverageState,
      created_at: '2026-07-15T10:30:04Z',
      claim_eligible: true,
    },
    {
      id: 'demo-evidence-pytest-test',
      contract_version: '0.1',
      canonical_skill_id: 'pytest',
      rule_id: 'python.pytest.test_function',
      detector_version: '0.1.0',
      repository: 'github:octocat/skillproof-demo',
      commit_sha: COMMIT_SHA,
      path: 'backend/tests/test_health.py',
      content_hash: '4ccbd1506528f89d043f7a652a784343af073bdb73beb9e16eb5f7b2f7952f67',
      start_line: 7,
      end_line: 10,
      redacted_excerpt:
        'def test_health(client):\n    response = client.get("/health")\n    assert response.status_code == 200',
      evidence_kind: 'test',
      confidence: 'high',
      coverage_state: coverageState,
      created_at: '2026-07-15T10:30:04Z',
      claim_eligible: true,
    },
    {
      id: 'demo-evidence-documentation',
      contract_version: '0.1',
      canonical_skill_id: 'python',
      rule_id: 'documentation.skill_reference',
      detector_version: '0.1.0',
      repository: 'github:octocat/skillproof-demo',
      commit_sha: COMMIT_SHA,
      path: 'README.md',
      content_hash: 'f9d3d01f163b439141e9277d6072473384212cb1e6c63e6930d8ee76daf3462c',
      start_line: 33,
      end_line: 33,
      redacted_excerpt: 'This project uses Python for its API and evidence detector modules.',
      evidence_kind: 'documentation_reference',
      confidence: 'low',
      coverage_state: coverageState,
      created_at: '2026-07-15T10:30:04Z',
      claim_eligible: false,
    },
  ]
}

export function createDemoResult(coverageState = 'complete') {
  const isPartial = coverageState === 'partial'
  const coverage = {
    state: isPartial ? 'partial' : 'complete',
    reasons: isPartial
      ? ['file_count_limit_reached', 'eligible_file_too_large']
      : [],
    files_discovered: isPartial ? 286 : 42,
    files_inspected: isPartial ? 40 : 26,
    files_skipped_by_policy: isPartial ? 211 : 16,
    bytes_inspected: isPartial ? 734112 : 184912,
    limits: {
      github_requests: 50,
      tree_entries: 10000,
      file_blobs: 40,
      per_file_bytes: 262144,
      total_file_bytes: 5242880,
      concurrency: 5,
      request_timeout_seconds: 10,
    },
    observed: {
      github_requests: isPartial ? 48 : 18,
      tree_entries: isPartial ? 286 : 42,
      file_blobs: isPartial ? 40 : 26,
      largest_file_bytes: isPartial ? 253901 : 28917,
      total_file_bytes: isPartial ? 734112 : 184912,
      maximum_concurrency: 5,
    },
  }

  return {
    scan: {
      id: `demo-${coverage.state}-scan`,
      repository: {
        provider: 'github',
        identity: 'github:octocat/skillproof-demo',
        owner: 'octocat',
        name: 'skillproof-demo',
        url: 'https://github.com/octocat/skillproof-demo',
      },
      status: 'completed',
      phase: 'complete',
      commit_sha: COMMIT_SHA,
      detector_version: '0.1.0',
      taxonomy_version: '0.1.0',
      redaction_version: '0.1.0',
      evidence_contract_version: '0.1',
      scan_policy_version: '0.1',
      coverage,
      error: null,
      created_at: '2026-07-15T10:30:00Z',
      started_at: '2026-07-15T10:30:01Z',
      completed_at: '2026-07-15T10:30:04Z',
    },
    evidence: makeEvidence(coverage.state),
  }
}
