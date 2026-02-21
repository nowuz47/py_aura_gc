# Submission Requirements Mapping

This reference maps generated submission artifacts (`vibecoding-result.mdx` and team card doc) to repository requirements.

## Source Mapping

| Source | Requirement | Generated Section |
| --- | --- | --- |
| `contents/docs/fairness-guide.mdx` 4.1 | 스킬 기반 제출 템플릿 생성/검증 | Entire document generation + validation gates |
| `contents/docs/fairness-guide.mdx` 4.2 | 수동 제출 이슈 템플릿과 동일 핵심 정보 | 프로젝트/팀 정보, 문제/해결, (선택) 기술 스택/검증/출처 |
| `contents/docs/how-to-participate.mdx` 4 | 제출 준비 항목 포함 | 제품 링크/실행 방법, 문제 정의, 데모 설명, 팀 소개/역할 |
| `source.config.ts` team schema | `/team` 카드 목록 데이터 | `contents/team/submission-<team>-<project>.mdx` frontmatter |

## Required Frontmatter

- `title: string`
- `summary: string`
- `description: string`
- `full?: boolean`

## Required Output Path

- `contents/docs/vibe-coding/<project-slug>.mdx`
- `contents/team/submission-<team-slug>-<project-slug>.mdx`

## Required Assets

- `contents/docs/vibe-coding/assets/<project-slug>/demo/README.md`
- `contents/docs/vibe-coding/assets/<project-slug>/evidence/README.md`
- `contents/docs/vibe-coding/assets/<project-slug>/team/README.md`

## Rendering Policy

- Optional sections with empty value or `미기재` are omitted from the final document.
- Submission checklist section is not rendered in `vibecoding-result.mdx`.
- Team card file is always generated so `/team` can render submission cards in the same format as existing team project cards.
