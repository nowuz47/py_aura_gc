---
name: hackathon-submission
description: Generate a submission-ready result document at contents/docs/vibe-coding/<project-slug>.mdx and open a fork-based PR to okky-lab/vibe-coding-hackathon. Use when users ask to prepare final hackathon submission docs, satisfy fairness-guide submission rules, satisfy how-to-participate submission preparation, or register a project submission with safe GitHub permissions.
---

# Hackathon Submission

## Overview

Create a `vibecoding-result.mdx` document and required assets under `contents/docs/vibe-coding`, and generate a matching team card document under `contents/team`, then open a PR to `okky-lab/vibe-coding-hackathon` via fork workflow.

Target repository is fixed to:

- `https://github.com/okky-lab/vibe-coding-hackathon`
- No runtime option is allowed to change the upstream repository.

## Required Inputs

Collect these required fields before running automation.

- `team_name`
- `project_name`
- `repo_url`
- `demo_url_or_run_method`
- `problem_definition`
- `one_liner`
- `team_roles`

Collect these recommended fields if available.

- `tech_stack`
- `run_verify`
- `demo_summary`
- `license_sources`
- `project_url`
- `team_role_label`
- `team_bio`
- `team_image_url`
- `submitted_at` (ISO 8601)
- `team_order` (integer)

Optional fields:

- `presentation_url`
- `extra_links`

Rendering rule:

- Optional sections are omitted when the value is empty or `미기재`.

## Execute Automation

Run the script from the skill root.

```bash
python3 scripts/create_submission_pr.py \
  --team-name "팀 OKKY" \
  --project-name "VibeShip" \
  --repo-url "https://github.com/example/project" \
  --demo-url-or-run-method "https://example.com/demo" \
  --problem-definition "해결하려는 문제를 작성" \
  --one-liner "한 줄 소개" \
  --team-roles "- 홍길동: FE\n- 김철수: BE"
```

For local rendering only (without GitHub PR):

```bash
python3 scripts/create_submission_pr.py \
  --team-name "팀 OKKY" \
  --project-name "VibeShip" \
  --repo-url "https://github.com/example/project" \
  --demo-url-or-run-method "README 실행 방법 참고" \
  --problem-definition "문제 정의" \
  --one-liner "한 줄 소개" \
  --team-roles "- 홍길동: FE" \
  --render-only-dir /tmp/hackathon-submission-test
```

For GitHub-inclusive dry-run (auth/fork/clone/render check without push/PR):

```bash
python3 scripts/create_submission_pr.py \
  --team-name "팀 OKKY" \
  --project-name "VibeShip" \
  --repo-url "https://github.com/example/project" \
  --demo-url-or-run-method "README 실행 방법 참고" \
  --problem-definition "문제 정의" \
  --one-liner "한 줄 소개" \
  --team-roles "- 홍길동: FE" \
  --github-dry-run
```

## Output Contract

The script must create:

- `contents/docs/vibe-coding/<project-slug>.mdx`
- `contents/docs/vibe-coding/assets/<project-slug>/demo/README.md`
- `contents/docs/vibe-coding/assets/<project-slug>/evidence/README.md`
- `contents/docs/vibe-coding/assets/<project-slug>/team/README.md`
- `contents/team/submission-<team-slug>-<project-slug>.mdx`

The script must ensure navigation metadata:

- `contents/docs/meta.json` includes `vibe-coding`
- `contents/docs/vibe-coding/meta.json` includes `<project-slug>`

## Validation Rules

Block generation if any validation fails.

- Frontmatter keys must be only `title`, `summary`, `description`, optional `full`
- `title`, `summary`, `description` must exist
- Core required sections must exist (project/team info, problem/solution, one-liner, team roles)
- Optional sections (`데모 설명`, `기술 스택`, `실행/검증 방법`, `라이선스/출처`, `발표 자료`, `추가 링크`) are rendered only when values are provided
- Team card frontmatter must satisfy `contents/team` schema (`name`, `role`, `bio` required and URL fields must be valid when provided)
- Existing document path must fail by default (unless `--update` is provided)

## Failure Fallback

When PR creation fails after commit/push, always return:

- Created commit SHA
- Pushed fork branch
- Manual PR compare URL

## GitHub Permission Collision Prevention (Final)

Always follow these rules:

1. Never push directly to `okky-lab/vibe-coding-hackathon`.
2. Always use `fork -> fork branch -> upstream PR`.
3. Let each participant use their own GitHub account and verify the active account with `gh auth status` before running.
4. Use branch pattern:
   - `submission/<team>-<project>-<YYYYMMDDHHmmss>-<6hex>`
5. Before PR creation, check for branch/PR duplication.
